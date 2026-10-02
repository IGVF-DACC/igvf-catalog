import json
from typing import Optional

from adapters.base import BaseAdapter
from adapters.helpers import (
    build_variant_coding_variant_key,
    build_variant_id,
    bulk_check_variants_in_arangodb,
    CHR_MAP,
    build_hgvs_from_spdi,
    load_variant,
)
from adapters.writer import Writer

# Sample file - file has 709 columns:
# #chr	pos(1-based)	ref	alt	aaref	aaalt	rs_dbSNP	hg19_chr	hg19_pos(1-based)	hg18_chr ... ALFA_Total_AN   ALFA_Total_AF dbNSFP_POPMAX_AF dbNSFP_POPMAX_AC dbNSFP_POPMAX_POP
# Y	2786989	C	A	X	Y	.	Y	2655030	Y	2715030	205	SRY	ENSG00000184895	ENST00000383070	ENSP00000372547 ... . . . . . .
# Y	2786990	T	C	X	W	.	Y	2655031	Y	2715031	205	SRY	ENSG00000184895	ENST00000383070	ENSP00000372547	... . . . . . .


class DbNSFP(BaseAdapter):
    ALLOWED_LABELS = ['coding_variants',
                      'coding_variants_proteins', 'variants_coding_variants', 'variants']
    CHUNK_SIZE = 6500
    SOURCE = 'dbNSFP 5.1a'
    SOURCE_URL = 'http://database.liulab.science/dbNSFP'

    def __init__(self, filepath=None, label='coding_variants', writer: Optional[Writer] = None, validate=False, **kwargs):
        super().__init__(filepath, label, writer, validate)
        self.written_variant_keys = set()

    def _get_schema_type(self):
        """Return schema type based on label."""
        if self.label in ('coding_variants', 'variants'):
            return 'nodes'
        else:
            return 'edges'

    def _get_collection_name(self):
        """Get collection based on label."""
        return self.label

    def multiple_records(self, data_line):
        indexes = [11, 12, 13, 14, 15, 17]
        for idx in indexes:
            if ';' in data_line[idx]:
                return True
        return False

    def breakdown_line(self, original_data_line):
        data_lines = []

        # original_data_line:  "1     69091    A    C    M    L    .    1    6901    1    58954    22;1    OR4F5;OR4FA    ..."
        data_line = []
        for column in original_data_line:
            data_line.append(column.strip().split(';'))

        # data_line example: [['1'], ['69091'], ['A'], ['C'], ['M'], ['L'], ['.'], ['1'], ... ,
        # ['69091'], ['1'], ['58954'], ['22', '1'], ['OR4F5', 'OR4FA'], ['ENSG00000186092', 'ENSG00000186090'], ...

        # data_lines output:
        # record 1: [['1'], ['69091'], ['A'], ['C'], ['M'], ['L'], ['.'], ['1'], ... ,
        # ['69091'], ['1'], ['58954'], ['22'], ['OR4F5'], ['ENSG00000186092'], ...

        # record 2: [['1'], ['69091'], ['A'], ['C'], ['M'], ['L'], ['.'], ['1'], ... ,
        # ['69091'], ['1'], ['58954'], ['1'], ['OR4FA'], ['ENSG00000186090'], ...

        # Assuming position is essential to define a coding variant
        # We are determining how many records are defined per row based on how many positions are listed
        # in the current example, max_idx = len(['22', '1']) = 2
        # assuming all related arrays will be of length 2
        max_idx = len(data_line[11])

        idx = 0
        while idx < max_idx:
            individual_data_line = []
            for column in data_line:
                # there are cases where we have missing values in a few scores
                # example: aapos: ['22', '1'] => max_idx = 2 and score: ['1']
                # assuming the missing value is the last one and filling up with None
                if len(column) > 1 and idx >= len(column):
                    individual_data_line.append(None)
                else:
                    individual_data_line.append(
                        column[idx] if len(column) > 1 else column[0])
            data_lines.append(individual_data_line)
            idx += 1

        return data_lines

    @staticmethod
    def data(data_line, pos):
        # '.' is equivalent to None in this dataset
        return data_line[pos] if data_line[pos] != '.' else None

    @staticmethod
    def long_data(data_line, pos):
        try:
            value = data_line[pos]

            # a few terms have a trailing ';', e.g. '0.489;', in rows with no need of breakdown
            # removing ; in that case:
            if value[-1] == ';':
                value = value[:-1]

            return float(value) if value != '.' and value != '.;' else None
        except:
            return None

    def build_coding_variant_key(self, data_line):
        data = DbNSFP.data
        long_data = DbNSFP.long_data

        aapos = long_data(data_line, 11)
        gene_name = data(data_line, 12)
        transcript_id = data(data_line, 14)
        hgvsp = data(data_line, 19)
        hgvs = data(data_line, 20)

        if hgvs is None:
            # basic format `chr:pos:ref:alt` to reuse hgvs builder method
            spdi = CHR_MAP['GRCh38'].get(
                data(data_line, 0)) + ':' + str(int(data(data_line, 1)) - 1) + ':' + data(data_line, 2) + ':' + data(data_line, 3)
            # creates hgvs.g
            hgvs = build_hgvs_from_spdi(spdi)

        # gene_name + transcript_id + hgvsp + hgvs + splicing (in case aapos == -1)
        key = gene_name + '_' + transcript_id + '_' + \
            (hgvsp or '') + '_' + (hgvs or '')
        if aapos == -1:
            key += '_splicing'

        key = key.replace('?', '!').replace('>', '-')
        return key, aapos, gene_name, transcript_id, hgvsp

    def write_coding_variant_record(self, data_line):
        data = DbNSFP.data
        long_data = DbNSFP.long_data
        key, aapos, gene_name, transcript_id, hgvsp = self.build_coding_variant_key(
            data_line)

        # deprecated - not in the database anymore
        if self.label == 'coding_variants_proteins':
            protein_id = data(data_line, 15)
            if not protein_id:
                return

            # removing possible isoform numbers. Example: P19367-4 => P19367
            if '-' in protein_id:
                protein_id = protein_id.split('-')[0]

            to_json = {
                '_from': 'coding_variants/' + key,
                '_to': 'proteins/' + protein_id,
                'type': 'protein coding' if (long_data(data_line, 11) != -1) else 'splicing',
                'name': 'variant of',
                'inverse_name': 'has variant',
                'source': DbNSFP.SOURCE,
                'source_url': DbNSFP.SOURCE_URL
            }
        else:
            ref = data(data_line, 4)
            alt = data(data_line, 5)
            if alt == 'X':
                alt = '*'
            if ref == 'X':
                ref = '*'

            to_json = {
                '_key': key,
                'name': key,
                'ref': ref,
                'alt': alt,
                'aapos': aapos,  # 1-based
                'gene_name': gene_name,
                'protein_name': data(data_line, 17),
                'protein_id': data(data_line, 15),
                'hgvsc': data(data_line, 20),
                'hgvsp': hgvsp,
                'refcodon': data(data_line, 28),
                'codonpos': long_data(data_line, 29),
                'transcript_id': transcript_id,
                'SIFT_score': long_data(data_line, 46),
                'SIFT4G_score': long_data(data_line, 49),
                'Polyphen2_HDIV_score': long_data(data_line, 52),
                'Polyphen2_HVAR_score': long_data(data_line, 55),
                'VEST4_score': long_data(data_line, 70),
                'REVEL_score': long_data(data_line, 85),
                'MutPred_score': long_data(data_line, 87),
                'BayesDel_addAF_score': long_data(data_line, 104),
                'BayesDel_noAF_score': long_data(data_line, 107),
                'VARITY_R_score': long_data(data_line, 116),
                'VARITY_ER_score': long_data(data_line, 118),
                'VARITY_R_LOO_score': long_data(data_line, 120),
                'VARITY_ER_LOO_score': long_data(data_line, 122),
                'ESM1b_score': long_data(data_line, 124),
                'AlphaMissense_score': long_data(data_line, 127),
                'CADD_raw_score': long_data(data_line, 142),
                'source': DbNSFP.SOURCE,
                'source_url': DbNSFP.SOURCE_URL
            }
        if self.validate:
            self.validate_doc(to_json)
        self.writer.write(json.dumps(to_json))
        self.writer.write('\n')

    def write_variants_coding_variants_edge(self, variant_id, data_line):
        data = DbNSFP.data
        long_data = DbNSFP.long_data
        key, *_ = self.build_coding_variant_key(data_line)

        to_json = {
            '_from': 'variants/' + variant_id,
            '_to': 'coding_variants/' + key,
            '_key': build_variant_coding_variant_key(variant_id, key),
            'source': DbNSFP.SOURCE,
            'source_url': DbNSFP.SOURCE_URL,
            'name': 'codes for',
            'inverse_name': 'encoded by',
            'chr': data(data_line, 0),
            # originally 1-based => 0-based
            'pos': long_data(data_line, 1) - 1,
            'ref': data(data_line, 2),
            'alt': data(data_line, 3),
        }
        if self.validate:
            self.validate_doc(to_json)
        self.writer.write(json.dumps(to_json))
        self.writer.write('\n')

    def write_missing_variants(self, rows_by_variant_id, loaded_variants):
        for variant_id, data_line in rows_by_variant_id:
            if variant_id in loaded_variants or variant_id in self.written_variant_keys:
                continue
            self.written_variant_keys.add(variant_id)

            chr, pos, ref, alt = data_line[0], data_line[1], data_line[2], data_line[3]
            variant_props, skipped = load_variant(f'{chr}-{pos}-{ref}-{alt}')
            if variant_props:
                variant_props.update({
                    'source': DbNSFP.SOURCE,
                    'source_url': DbNSFP.SOURCE_URL,
                })
                if self.validate:
                    self.validate_doc(variant_props)
                self.writer.write(json.dumps(variant_props))
                self.writer.write('\n')
            elif skipped:
                self.logger.warning(
                    f"Invalid variant: {skipped['variant_id']} - {skipped['reason']}")

    def process_variant_chunk(self, chunk):
        rows_by_variant_id = []
        for data_line in chunk:
            try:
                variant_id = build_variant_id(
                    data_line[0],
                    data_line[1],  # 1-based
                    data_line[2],
                    data_line[3]
                )
            except Exception as e:
                self.logger.warning(
                    f'Skipping row - unable to build variant id (chr={data_line[0]}, pos={data_line[1]}, ref={data_line[2]}, alt={data_line[3]}): {e}')
                continue
            rows_by_variant_id.append((variant_id, data_line))

        if not rows_by_variant_id:
            return

        loaded_variants = bulk_check_variants_in_arangodb(
            list({variant_id for variant_id, _ in rows_by_variant_id}),
            check_by='_key',
        )

        if self.label == 'variants':
            self.write_missing_variants(rows_by_variant_id, loaded_variants)
            return

        skipped_missing = 0
        for variant_id, data_line in rows_by_variant_id:
            if variant_id not in loaded_variants:
                skipped_missing += 1
                continue
            self.write_variants_coding_variants_edge(variant_id, data_line)

        if skipped_missing:
            self.logger.warning(
                f'Skipped {skipped_missing} row(s) - variant not found in variants collection')

    def parse(self):
        chunk = []
        for line in open(self.filepath, 'r'):
            if line.startswith('#chr'):
                continue

            original_data_line = line.strip().split('\t')

            if self.multiple_records(original_data_line):
                data_lines = self.breakdown_line(original_data_line)
            else:
                data_lines = [original_data_line]

            for data_line in data_lines:
                if self.label in ('variants_coding_variants', 'variants'):
                    chunk.append(data_line)
                    if len(chunk) >= DbNSFP.CHUNK_SIZE:
                        self.process_variant_chunk(chunk)
                        chunk = []
                else:
                    self.write_coding_variant_record(data_line)

        if chunk:
            self.process_variant_chunk(chunk)
