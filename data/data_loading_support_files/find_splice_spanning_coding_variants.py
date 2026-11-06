# Find enumerated coding variants (from ESM / MutPred2 mapping files) with an invalid genomic change.
#
# enumerate_coding_variants_all_mappings.py initially builds the SPDI of a delins as one contiguous genomic stretch starting at ref_pos.
# When the changed codon bases span an exon/intron junction, the genomic bases are not contiguous, so the SPDI is not a valid
# genome change, e.g. ENSP00000263080 p.Gly79Val -> NC_000017.11:3476394:GC:TA (GG|intron|C on the codon).
# SNVs (and delins whose changed bases fall in a single exon) are mapped correctly and are not reported.
#
# For each bad coding variant, candidate SNVs are the alt codons (same aa change) differing from codon_ref at one base;
# they are looked up by _key in coding_variants, e.g. ASPA_ENST00000263080_p.Gly79Val_c.236G-T,
# or in the dbNSFP splicing form (aapos == -1, no hgvsp) e.g. A1BG_ENST00000263100__NC_000019.10:g.58347031T-A_splicing
#
# Usage (run from data/, DB connection is read from ../config/development.json):
# python data_loading_support_files/find_splice_spanning_coding_variants.py \
#   --mapping-files ESM_1v_IGVFFI8105TNNO_mappings.tsv.gz mutpred2_IGVFFI6893ZOAA_mappings.tsv.gz \
#   --output splice_spanning_coding_variants.tsv

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

from adapters.helpers import convert_aa_letter_code_and_Met1  # noqa: E402
from db.arango_db import ArangoDB  # noqa: E402

csv.field_size_limit(sys.maxsize)

# both ESM and MutPred2 mapping files share the first 11 columns
MAPPING_FILE_HEADER = ['transcript_id', 'aa_change', 'mutation_ids', 'hgvsc_ids', 'spdi_ids',
                       'hgvsg_ids', 'alt_codons', 'codon_positions', 'codon_ref', 'protein_id', 'protein_name']
PHENOTYPE_TERM = 'GO_0003674'
FILE_ACCESSION_PATTERN = re.compile(r'(?:IGVFFI|ENCFF)[A-Z0-9]+')
HGVSC_PATTERN = re.compile(
    r'^c\.(\d+)(?:_(\d+)delins([ACGT]+)|([ACGT])-([ACGT]))$')
AA_POS_PATTERN = re.compile(r'^(?:p\.)?[A-Za-z]+(\d+)')
TRANSCRIPT_CACHE_SIZE = 100

OUTPUT_HEADER = ['source_file', 'transcript_id', 'aa_change', 'bad_coding_variant_id', 'bad_spdi',
                 'phenotype_edge_key', 'codon_ref', 'alt_codon', 'candidate_snv_hgvsg', 'dbnsfp_snv_keys', 'dbnsfp_snv_sources']

COMPLEMENT = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}


def reverse_complement(seq):
    return ''.join(COMPLEMENT.get(base, base) for base in reversed(seq))


class TranscriptStructures:
    '''CDS coordinates per transcript from genes_structure, built the same way as get_exon_coordinates in run_parallel_mapping_mutpred2.py.'''

    QUERY = '''
        FOR s IN genes_structure
            FILTER s.transcript_id == @transcript_id AND s.type == 'CDS'
            RETURN { chr: s.chr, start: s.start, end: s.end, strand: s.strand, exon_number: s.exon_number }
    '''

    def __init__(self, db):
        self.db = db
        self.cache = OrderedDict()

    def get(self, transcript_id):
        if transcript_id in self.cache:
            self.cache.move_to_end(transcript_id)
            return self.cache[transcript_id]

        CDS = {}
        for structure in self.db.aql.execute(self.QUERY, bind_vars={'transcript_id': transcript_id}):
            CDS[int(structure['exon_number'])] = structure

        result = None
        if CDS:
            exons_coordinates = []
            for i in range(min(CDS.keys()), max(CDS.keys()) + 1):
                if i not in CDS:
                    continue
                if CDS[i]['strand'] == '+':
                    exons_coordinates.extend(
                        range(CDS[i]['start'], CDS[i]['end']))
                else:
                    exons_coordinates.extend(
                        reversed(range(CDS[i]['start'], CDS[i]['end'])))
            # 0-based transcript index i where exons_coordinates[i] and [i + 1] are not adjacent on the genome
            junctions = [i for i in range(len(exons_coordinates) - 1)
                         if abs(exons_coordinates[i + 1] - exons_coordinates[i]) != 1]
            result = {
                'exons_coordinates': exons_coordinates,
                'junctions': junctions,
                'strand': next(iter(CDS.values()))['strand']
            }

        self.cache[transcript_id] = result
        if len(self.cache) > TRANSCRIPT_CACHE_SIZE:
            self.cache.popitem(last=False)
        return result


class DbNSFPSplicingVariants:
    '''Look up dbNSFP coding variants at splice sites by _key (filtering coding_variants on transcript_id is a full collection scan).'''

    def __init__(self, db):
        self.collection = db.collection('coding_variants')

    def existing_keys(self, gene, transcript_id, hgvsp, candidates):
        # dbNSFP key: gene + '_' + transcript_id + '_' + hgvsp + '_' + hgvsc, e.g. ASPA_ENST00000263080_p.Gly79Val_c.236G-T
        # or when hgvsp is missing: gene + '_' + transcript_id + '__' + (hgvsc or hgvsg) + '_splicing'
        # e.g. A1BG_ENST00000263100__NC_000019.10:g.58347031T-A_splicing
        keys = []
        for hgvsg, hgvsc in candidates:
            keys.append(convert_aa_letter_code_and_Met1(
                f'{gene}_{transcript_id}_p.{hgvsp}_{hgvsc}'))
            keys.append(f'{gene}_{transcript_id}__{hgvsg}_splicing')
            keys.append(f'{gene}_{transcript_id}__{hgvsc}_splicing')
        if not keys:
            return []
        found = {doc['_key']: doc.get('source')
                 for doc in self.collection.get_many(keys)}
        return [(key, found[key]) for key in keys if key in found]


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
    '''SNVs producing the same aa change: alt codons differing from codon_ref at one base. Returns list of (hgvsg_key_form, hgvsc_key_form).'''
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


def process_mapping_file(mapping_file, structures, dbnsfp, writer, stats, transcripts_filter, max_rows=None):
    source_file = os.path.basename(mapping_file)
    file_accession = FILE_ACCESSION_PATTERN.search(source_file).group(0)
    missing_transcripts = set()

    with gzip.open(mapping_file, 'rt') as map_file:
        map_csv = csv.reader(map_file, delimiter='\t')
        for row_idx, row in enumerate(map_csv):
            if max_rows is not None and row_idx >= max_rows:
                break
            stats[source_file + ' rows read'] += 1
            if row_idx and row_idx % 1000000 == 0:
                print(
                    f'{source_file}: {row_idx} rows processed, {stats[source_file + " bad coding variants"]} bad coding variants', flush=True)

            row = dict(zip(MAPPING_FILE_HEADER, row))
            hgvsc_ids = row['hgvsc_ids'].split(',')
            # only delins can be wrongly mapped
            if 'delins' not in row['hgvsc_ids']:
                continue

            transcript_id = row['transcript_id'].split('.')[0]
            if transcripts_filter and transcript_id not in transcripts_filter:
                continue

            aa_pos_match = AA_POS_PATTERN.match(row['aa_change'])
            if not aa_pos_match:
                stats['unparsable aa_change'] += 1
                continue
            aa_pos = int(aa_pos_match.group(1))

            structure = structures.get(transcript_id)
            if structure is None:
                if transcript_id not in missing_transcripts:
                    missing_transcripts.add(transcript_id)
                    stats[source_file +
                          ' transcripts missing in genes_structure'] += 1
                continue

            codon_start = (aa_pos - 1) * 3 + 1
            if codon_start + 2 > len(structure['exons_coordinates']):
                stats[source_file + ' codon out of CDS range'] += 1
                continue
            # quick skip: codon does not span a junction
            if not crosses_junction(structure['junctions'], codon_start, codon_start + 2):
                continue

            stats[source_file + ' rows at splice codons'] += 1
            mutation_ids = row['mutation_ids'].split(',')
            spdi_ids = row['spdi_ids'].split(',')
            alt_codons = row['alt_codons'].split(',')
            chrom_refseq = spdi_ids[0].split(':')[0]
            snvs = None

            for mutation_id, hgvsc, spdi, alt_codon in zip(mutation_ids, hgvsc_ids, spdi_ids, alt_codons):
                span = changed_span(hgvsc)
                if span is None:
                    stats[source_file + ' unparsable hgvsc'] += 1
                    continue
                c_start, c_end, is_delins = span

                # consistency check against how the mapping script set ref_pos, flags a different gene structure version
                exons_coordinates = structure['exons_coordinates']
                expected_pos = exons_coordinates[c_start -
                                                 1] if structure['strand'] == '+' else exons_coordinates[c_end - 1]
                if int(spdi.split(':')[1]) != expected_pos:
                    stats[source_file +
                          ' spdi position mismatch with genes_structure'] += 1
                    continue

                if not is_delins or not crosses_junction(structure['junctions'], c_start, c_end):
                    continue

                if snvs is None:
                    candidates = candidate_snvs(
                        row['codon_ref'], alt_codons, aa_pos, structure, chrom_refseq)
                    matched = dbnsfp.existing_keys(
                        mutation_id.split('_')[0], transcript_id, re.sub(r'^p\.', '', row['aa_change']), candidates)
                    snvs = ([c[0] for c in candidates], matched)

                coding_variant_id = convert_aa_letter_code_and_Met1(
                    re.sub(r'(ENST\d+)\.\d+', r'\1', mutation_id))
                writer.writerow([
                    source_file,
                    transcript_id,
                    row['aa_change'],
                    coding_variant_id,
                    spdi,
                    '_'.join(
                        [coding_variant_id, PHENOTYPE_TERM, file_accession]),
                    row['codon_ref'],
                    alt_codon,
                    ','.join(snvs[0]),
                    ','.join(key for key, _ in snvs[1]),
                    ','.join(str(source) for _, source in snvs[1])
                ])
                stats[source_file + ' bad coding variants'] += 1
                stats[source_file + ' bad coding variants with dbNSFP SNV' if snvs[1]
                      else source_file + ' bad coding variants without dbNSFP SNV'] += 1


def main():
    parser = argparse.ArgumentParser(
        description='Find enumerated coding variants with invalid delins spanning exon/intron junctions.')
    parser.add_argument('--mapping-files', nargs='+', required=True,
                        help='enumerated mapping files, e.g. ESM_1v_IGVFFI8105TNNO_mappings.tsv.gz mutpred2_IGVFFI6893ZOAA_mappings.tsv.gz')
    parser.add_argument('--output', default='splice_spanning_coding_variants.tsv',
                        help='output TSV of bad coding variants')
    parser.add_argument('--transcripts', nargs='*', default=None,
                        help='only check these transcript ids (without version), for testing')
    parser.add_argument('--max-rows', type=int, default=None,
                        help='only read the first N rows of each mapping file, for testing')
    args = parser.parse_args()

    db = ArangoDB().get_igvf_connection()
    structures = TranscriptStructures(db)
    dbnsfp = DbNSFPSplicingVariants(db)
    transcripts_filter = set(args.transcripts) if args.transcripts else None
    stats = Counter()

    with open(args.output, 'w', newline='') as out:
        writer = csv.writer(out, delimiter='\t')
        writer.writerow(OUTPUT_HEADER)
        for mapping_file in args.mapping_files:
            start_time = time.time()
            process_mapping_file(mapping_file, structures,
                                 dbnsfp, writer, stats, transcripts_filter, args.max_rows)
            stats[os.path.basename(mapping_file) +
                  ' seconds'] = round(time.time() - start_time)

    for name, count in sorted(stats.items()):
        print(f'{name}: {count}')


if __name__ == '__main__':
    main()
