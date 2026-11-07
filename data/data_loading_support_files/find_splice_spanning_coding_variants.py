# Find enumerated coding variants (from ESM / MutPred2 mapping files) with an invalid genomic change, and write cleaned mapping files.
#
# enumerate_coding_variants_all_mappings.py initially builds the SPDI of a delins as one contiguous genomic stretch starting at ref_pos.
# When the changed codon bases span an exon/intron junction, the genomic bases are not contiguous, so the SPDI is not a valid
# genome change, e.g. ENSP00000263080 p.Gly79Val -> NC_000017.11:3476394:GC:TA (GG|intron|C on the codon).
# SNVs (and delins whose changed bases fall in a single exon) are mapped correctly and are not reported.
#
# For each bad coding variant, candidate SNVs are the alt codons (same aa change) differing from codon_ref at one base;
# they are looked up by _key in coding_variants, e.g. ASPA_ENST00000263080_p.Gly79Val_c.236G-T (from dbNSFP, or novel SNVs enumerated
# from ESM / MutPred2 with source IGVF). dbNSFP *_splicing variants are not checked: they are all intronic splice-site SNVs
# (1-2 bp outside CDS), so they never overlap with enumerated coding variants.
#
# Outputs, per mapping file:
#   splice_spanning_coding_variants_<accession>.tsv: bad coding variants, used for deleting records in the database
#   <mapping file>.cleaned.tsv.gz (with --cleaned-output-dir): mapping file with bad entries removed from all comma-separated columns,
#   rows with no entries left are dropped, other columns (e.g. scores) are kept as is
#
# Read-only on the database. DB connection is read from ../config/development.json.
#
# Usage (run from data/):
# python data_loading_support_files/find_splice_spanning_coding_variants.py \
#   --mapping-files ~/dataset/ESM_1v_IGVFFI8105TNNO_mappings.tsv.gz \
#   --output-dir . --cleaned-output-dir ~/dataset/cleaned

import argparse
import csv
import gzip
import os
import re
import sys
import time
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

from arango.exceptions import AQLQueryExecuteError, DocumentGetError  # noqa: E402
from adapters.helpers import convert_aa_letter_code_and_Met1  # noqa: E402
from db.arango_db import ArangoDB  # noqa: E402

csv.field_size_limit(sys.maxsize)

# both ESM and MutPred2 mapping files share the first 11 columns
MAPPING_FILE_HEADER = ['transcript_id', 'aa_change', 'mutation_ids', 'hgvsc_ids', 'spdi_ids',
                       'hgvsg_ids', 'alt_codons', 'codon_positions', 'codon_ref', 'protein_id', 'protein_name']
# columns holding one comma-separated entry per enumerated genetic variant
LIST_COLUMNS = [2, 3, 4, 5, 6, 7]
PHENOTYPE_TERM = 'GO_0003674'
FILE_ACCESSION_PATTERN = re.compile(r'(?:IGVFFI|ENCFF)[A-Z0-9]+')
HGVSC_PATTERN = re.compile(
    r'^c\.(\d+)(?:_(\d+)delins([ACGT]+)|([ACGT])-([ACGT]))$')
AA_POS_PATTERN = re.compile(r'^(?:p\.)?[A-Za-z]+(\d+)')

TRANSCRIPT_CACHE_SIZE = 200
TRANSCRIPTS_PER_QUERY = 50
ROWS_PER_BATCH = 20000
KEYS_PER_GET_MANY = 1000
MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds, doubled after each retry

OUTPUT_HEADER = ['source_file', 'transcript_id', 'aa_change', 'bad_coding_variant_id', 'bad_spdi',
                 'phenotype_edge_key', 'codon_ref', 'alt_codon', 'candidate_snv_hgvsg', 'matched_snv_keys', 'matched_snv_sources']

COMPLEMENT = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}


def reverse_complement(seq):
    return ''.join(COMPLEMENT.get(base, base) for base in reversed(seq))


def transcript_id_no_version(transcript_id):
    # keep _PAR_Y suffix, it's part of transcript_id in genes_structure, e.g. ENST00000334651.11_PAR_Y -> ENST00000334651_PAR_Y
    return re.sub(r'(ENST\d+)\.\d+', r'\1', transcript_id)


def coding_variant_key(mutation_id):
    '''Mutation id from mapping file -> coding_variants _key as loaded by the adapters,
    e.g. DHRSX_ENST00000334651.11_PAR_Y_p.Met1Ala_c.1_3delinsGCA -> DHRSX_ENST00000334651_PAR_Y_p.Met1!_c.1_3delinsGCA'''
    mutation_id = transcript_id_no_version(mutation_id)
    # convert_aa_letter_code_and_Met1 expects gene_transcript_hgvsp_hgvsc
    par_y = '_PAR_Y_' in mutation_id
    if par_y:
        mutation_id = mutation_id.replace('_PAR_Y_', '_', 1)
    key = convert_aa_letter_code_and_Met1(mutation_id)
    if par_y:
        gene, transcript_id, rest = key.split('_', 2)
        key = '_'.join([gene, transcript_id + '_PAR_Y', rest])
    return key


def with_retry(func, *args, **kwargs):
    # db-dev returns 504 on slow requests now and then
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except (AQLQueryExecuteError, DocumentGetError, ConnectionAbortedError) as e:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = RETRY_DELAY * 2 ** attempt
            print(
                f'Retry {attempt + 1}/{MAX_RETRIES - 1} in {wait}s: {e}', flush=True)
            time.sleep(wait)


class TranscriptStructures:
    '''CDS coordinates per transcript from genes_structure, built the same way as get_exon_coordinates in run_parallel_mapping_mutpred2.py.'''

    QUERY = '''
        FOR s IN genes_structure
            FILTER s.transcript_id IN @transcript_ids AND s.type == 'CDS'
            RETURN { transcript_id: s.transcript_id, start: s.start, end: s.end, strand: s.strand, exon_number: s.exon_number }
    '''

    def __init__(self, db):
        self.db = db
        self.cache = OrderedDict()

    def prefetch(self, transcript_ids):
        # mark cached transcripts of this batch as recently used so trimming below does not evict them
        for t in transcript_ids:
            if t in self.cache:
                self.cache.move_to_end(t)
        missing = [t for t in transcript_ids if t not in self.cache]
        for i in range(0, len(missing), TRANSCRIPTS_PER_QUERY):
            batch = missing[i:i + TRANSCRIPTS_PER_QUERY]
            CDS_by_transcript = {t: {} for t in batch}
            cursor = with_retry(self.db.aql.execute, self.QUERY, bind_vars={
                                'transcript_ids': batch}, batch_size=10000)
            for structure in cursor:
                CDS_by_transcript[structure['transcript_id']][int(
                    structure['exon_number'])] = structure
            for transcript_id, CDS in CDS_by_transcript.items():
                self.cache[transcript_id] = self.build(CDS)
                self.cache.move_to_end(transcript_id)
        while len(self.cache) > max(TRANSCRIPT_CACHE_SIZE, len(transcript_ids)):
            self.cache.popitem(last=False)

    @staticmethod
    def build(CDS):
        if not CDS:
            return None
        exons_coordinates = []
        for i in range(min(CDS.keys()), max(CDS.keys()) + 1):
            if i not in CDS:
                continue
            if CDS[i]['strand'] == '+':
                exons_coordinates.extend(range(CDS[i]['start'], CDS[i]['end']))
            else:
                exons_coordinates.extend(
                    reversed(range(CDS[i]['start'], CDS[i]['end'])))
        # 0-based transcript index i where exons_coordinates[i] and [i + 1] are not adjacent on the genome
        junctions = [i for i in range(len(exons_coordinates) - 1)
                     if abs(exons_coordinates[i + 1] - exons_coordinates[i]) != 1]
        return {
            'exons_coordinates': exons_coordinates,
            'junctions': junctions,
            'strand': next(iter(CDS.values()))['strand']
        }

    def get(self, transcript_id):
        return self.cache.get(transcript_id)


def existing_coding_variants(db, keys):
    '''Return {_key: source} for keys found in coding_variants.'''
    collection = db.collection('coding_variants')
    found = {}
    keys = list(dict.fromkeys(keys))
    for i in range(0, len(keys), KEYS_PER_GET_MANY):
        for doc in with_retry(collection.get_many, keys[i:i + KEYS_PER_GET_MANY]):
            found[doc['_key']] = doc.get('source')
    return found


def changed_span(hgvsc):
    '''Return (c_start, c_end, is_delins) 1-based on the transcript, or None if hgvsc can not be parsed.'''
    match = HGVSC_PATTERN.match(hgvsc)
    if not match:
        return None
    c_start = int(match.group(1))
    if match.group(2):
        return c_start, int(match.group(2)), True
    return c_start, c_start, False


def crosses_junction(junctions, c_start, c_end):
    # transcript positions c_start..c_end (1-based) are contiguous on the genome unless a junction index falls in [c_start - 1, c_end - 2]
    return any(c_start - 1 <= j <= c_end - 2 for j in junctions)


def candidate_snvs(codon_ref, alt_codons, aa_pos, structure, chrom_refseq):
    '''SNVs producing the same aa change: alt codons differing from codon_ref at one base. Returns list of (hgvsg, hgvsc) in key form.'''
    exons_coordinates = structure['exons_coordinates']
    codon_start = (aa_pos - 1) * 3 + 1
    candidates = []
    for alt_codon in alt_codons:
        diffs = [i for i in range(3) if codon_ref[i] != alt_codon[i]]
        if len(diffs) != 1:
            continue
        offset = diffs[0]
        c_pos = codon_start + offset
        g_pos = exons_coordinates[c_pos - 1]  # 0-based
        ref, alt = codon_ref[offset], alt_codon[offset]
        if structure['strand'] == '-':
            g_ref, g_alt = reverse_complement(ref), reverse_complement(alt)
        else:
            g_ref, g_alt = ref, alt
        candidates.append((f'{chrom_refseq}:g.{g_pos + 1}{g_ref}-{g_alt}',
                           f'c.{c_pos}{ref}-{alt}'))
    return candidates


class MappingFileChecker:
    def __init__(self, mapping_file, structures, db, bad_writer, cleaned_file, stats, transcripts_filter):
        self.source_file = os.path.basename(mapping_file)
        self.file_accession = FILE_ACCESSION_PATTERN.search(
            self.source_file).group(0)
        self.structures = structures
        self.db = db
        self.bad_writer = bad_writer
        self.cleaned_file = cleaned_file
        self.stats = stats
        self.transcripts_filter = transcripts_filter

    def count(self, name, n=1):
        self.stats[self.source_file + ' ' + name] += n

    def find_bad_entries(self, row):
        '''Return (bad entry indices, info needed to report them) for one mapping row.'''
        if 'delins' not in row[3]:
            return [], None
        transcript_id = transcript_id_no_version(row[0])
        if self.transcripts_filter and transcript_id not in self.transcripts_filter:
            return [], None

        aa_pos_match = AA_POS_PATTERN.match(row[1])
        if not aa_pos_match:
            self.count('unparsable aa_change')
            return [], None
        aa_pos = int(aa_pos_match.group(1))

        structure = self.structures.get(transcript_id)
        if structure is None:
            self.count('rows of transcripts missing in genes_structure')
            return [], None

        codon_start = (aa_pos - 1) * 3 + 1
        if codon_start + 2 > len(structure['exons_coordinates']):
            self.count('codon out of CDS range')
            return [], None
        # quick skip: codon does not span a junction
        if not crosses_junction(structure['junctions'], codon_start, codon_start + 2):
            return [], None

        self.count('rows at splice codons')
        mutation_ids, hgvsc_ids, spdi_ids = row[2].split(
            ','), row[3].split(','), row[4].split(',')
        alt_codons = row[6].split(',')
        if len({len(row[i].split(',')) for i in LIST_COLUMNS}) != 1:
            self.count('rows with misaligned list columns (kept as is)')
            return [], None

        exons_coordinates = structure['exons_coordinates']
        bad_indices = []
        for i, (hgvsc, spdi) in enumerate(zip(hgvsc_ids, spdi_ids)):
            span = changed_span(hgvsc)
            if span is None:
                self.count('unparsable hgvsc')
                continue
            c_start, c_end, is_delins = span

            # consistency check against how the mapping script set ref_pos, flags a different gene structure version
            expected_pos = exons_coordinates[c_start -
                                             1] if structure['strand'] == '+' else exons_coordinates[c_end - 1]
            if int(spdi.split(':')[1]) != expected_pos:
                self.count(
                    'spdi position mismatch with genes_structure (kept)')
                continue

            if is_delins and crosses_junction(structure['junctions'], c_start, c_end):
                bad_indices.append(i)

        if not bad_indices:
            return [], None

        gene = mutation_ids[0].split('_')[0]
        hgvsp = re.sub(r'^p\.', '', row[1])
        candidates = candidate_snvs(
            row[8], alt_codons, aa_pos, structure, spdi_ids[0].split(':')[0])
        # dbNSFP key: gene + '_' + transcript_id + '_' + hgvsp + '_' + hgvsc, e.g. ASPA_ENST00000263080_p.Gly79Val_c.236G-T
        snv_keys = [coding_variant_key(
            f'{gene}_{transcript_id}_p.{hgvsp}_{hgvsc}') for _, hgvsc in candidates]
        return bad_indices, (transcript_id, candidates, snv_keys)

    def process_batch(self, rows):
        transcript_ids = list(dict.fromkeys(
            transcript_id_no_version(row[0]) for row in rows if 'delins' in row[3]))
        if self.transcripts_filter:
            transcript_ids = [
                t for t in transcript_ids if t in self.transcripts_filter]
        self.structures.prefetch(transcript_ids)

        results = []
        for row in rows:
            try:
                results.append(self.find_bad_entries(row))
            except Exception as e:
                # don't stop a multi-hour run on one unexpected row, it's kept as is in the cleaned file
                print(
                    f'Failed on row {row[0]} {row[1]}, kept as is: {e!r}', flush=True)
                self.count('rows failed (kept as is)')
                results.append(([], None))
        found = existing_coding_variants(
            self.db, [key for _, info in results if info for key in info[2]])

        for row, (bad_indices, info) in zip(rows, results):
            if bad_indices:
                self.write_bad_entries(row, bad_indices, info, found)
            if self.cleaned_file:
                self.write_cleaned_row(row, bad_indices)

    def write_bad_entries(self, row, bad_indices, info, found):
        transcript_id, candidates, snv_keys = info
        matched = [key for key in snv_keys if key in found]
        mutation_ids, spdi_ids, alt_codons = row[2].split(
            ','), row[4].split(','), row[6].split(',')
        for i in bad_indices:
            coding_variant_id = coding_variant_key(mutation_ids[i])
            self.bad_writer.writerow([
                self.source_file,
                transcript_id,
                row[1],
                coding_variant_id,
                spdi_ids[i],
                '_'.join(
                    [coding_variant_id, PHENOTYPE_TERM, self.file_accession]),
                row[8],
                alt_codons[i],
                ','.join(hgvsg for hgvsg, _ in candidates),
                ','.join(matched),
                ','.join(str(found[key]) for key in matched)
            ])
        self.count('bad coding variants', len(bad_indices))
        self.count('bad coding variants with matched SNV' if matched
                   else 'bad coding variants without matched SNV', len(bad_indices))

    def write_cleaned_row(self, row, bad_indices):
        if bad_indices:
            bad = set(bad_indices)
            row = list(row)
            for col in LIST_COLUMNS:
                row[col] = ','.join(entry for i, entry in enumerate(
                    row[col].split(',')) if i not in bad)
            if not row[2]:
                self.count('cleaned rows dropped (no entries left)')
                return
            self.count('cleaned rows with entries removed')
        # write fields as is, csv.writer would add quotes around JSON fields (e.g. MutPred2 Mechanisms)
        self.cleaned_file.write('\t'.join(row) + '\n')
        self.count('cleaned rows written')

    def run(self, mapping_file, max_rows):
        with gzip.open(mapping_file, 'rt') as map_file:
            map_csv = csv.reader(map_file, delimiter='\t')
            rows = []
            for row_idx, row in enumerate(map_csv):
                if max_rows is not None and row_idx >= max_rows:
                    break
                rows.append(row)
                if len(rows) >= ROWS_PER_BATCH:
                    self.process_batch(rows)
                    self.count('rows read', len(rows))
                    rows = []
                    if self.stats[self.source_file + ' rows read'] % 1000000 == 0:
                        print(f'{self.source_file}: {self.stats[self.source_file + " rows read"]} rows processed, '
                              f'{self.stats[self.source_file + " bad coding variants"]} bad coding variants', flush=True)
            if rows:
                self.process_batch(rows)
                self.count('rows read', len(rows))


def main():
    parser = argparse.ArgumentParser(
        description='Find enumerated coding variants with invalid delins spanning exon/intron junctions, and write cleaned mapping files.')
    parser.add_argument('--mapping-files', nargs='+', required=True,
                        help='enumerated mapping files, e.g. ESM_1v_IGVFFI8105TNNO_mappings.tsv.gz mutpred2_IGVFFI6893ZOAA_mappings.tsv.gz')
    parser.add_argument('--output-dir', default='.',
                        help='directory for splice_spanning_coding_variants_<accession>.tsv')
    parser.add_argument('--cleaned-output-dir', default=None,
                        help='if set, write <mapping file>.cleaned.tsv.gz with bad entries removed to this directory')
    parser.add_argument('--transcripts', nargs='*', default=None,
                        help='only check these transcript ids (without version), for testing')
    parser.add_argument('--max-rows', type=int, default=None,
                        help='only read the first N rows of each mapping file, for testing')
    args = parser.parse_args()

    db = ArangoDB().get_igvf_connection()
    structures = TranscriptStructures(db)
    transcripts_filter = set(args.transcripts) if args.transcripts else None
    stats = Counter()

    for mapping_file in args.mapping_files:
        source_file = os.path.basename(mapping_file)
        file_accession = FILE_ACCESSION_PATTERN.search(source_file).group(0)
        bad_path = os.path.join(
            args.output_dir, f'splice_spanning_coding_variants_{file_accession}.tsv')
        cleaned_file = None
        if args.cleaned_output_dir:
            os.makedirs(args.cleaned_output_dir, exist_ok=True)
            cleaned_path = os.path.join(args.cleaned_output_dir, re.sub(
                r'\.tsv\.gz$', '', source_file) + '.cleaned.tsv.gz')
            cleaned_file = gzip.open(cleaned_path, 'wt')

        start_time = time.time()
        with open(bad_path, 'w', newline='') as out:
            bad_writer = csv.writer(out, delimiter='\t')
            bad_writer.writerow(OUTPUT_HEADER)
            MappingFileChecker(mapping_file, structures, db, bad_writer, cleaned_file, stats,
                               transcripts_filter).run(mapping_file, args.max_rows)
        if cleaned_file:
            cleaned_file.close()
        stats[source_file + ' seconds'] = round(time.time() - start_time)

    for name, count in sorted(stats.items()):
        print(f'{name}: {count}')


if __name__ == '__main__':
    main()
