import csv
import json
import os
import gzip
import requests
from adapters.helpers import bulk_check_spdis_in_arangodb, CHR_MAP, load_variant

from typing import Optional

from adapters.writer import Writer

# Example rows from SGE file (IGVFFI9974PZRX.tsv.gz)
# chrom	pos	ref	alt	exon	target	consequence	score	standard_error	95_ci_upper	95_ci_lower	amino_acid_change	hgvs_p	functional_consequence	functional_consequence_zscore	variant_qc_flag	snvlib_lib1	snvlib_lib2	D05_R1_lib1	D05_R1_lib2	D05_R2_lib1	D05_R2_lib2	D05_R3_lib1	D05_R3_lib2	D13_R1_lib1	D13_R1_lib2	D13_R2_lib1	D13_R2_lib2	D13_R3_lib1	D13_R3_lib2
# chr16	23603562	G	A	PALB2_X13	PALB2_X13A	missense_variant	-0.140561	0.0469519	-0.0485354	-0.232587	P1153L	ENSP00000261584.4:p.Pro1153Leu	functionally_abnormal	-4.24559	PASS	1155		114		326		361		158		297		512


class SGE:
    ALLOWED_LABELS = ['variants', 'variants_phenotypes',
                      'variants_phenotypes_coding_variants']
    SOURCE = 'IGVF'
    PHENOTYPE_TERM = 'NCIT_C16407'
    FLOAT_FIELDS = ['score', 'standard_error', '95_ci_upper',
                    '95_ci_lower', 'functional_consequence_zscore']

    def __init__(self, filepath, label='variants_phenotypes', writer: Optional[Writer] = None, **kwargs):
        if label not in SGE.ALLOWED_LABELS:
            raise ValueError('Invalid label. Allowed values: ' +
                             ','.join(SGE.ALLOWED_LABELS))

        self.filepath = filepath
        self.file_accession = os.path.basename(self.filepath).split('.')[0]
        self.source_url = 'https://data.igvf.org/tabular-files/' + self.file_accession
        self.label = label
        self.writer = writer

    # each SGE file has 800 ~ 10,000 variants in total -> feasible to validate them all at once
    def validate_variants(self):
        print(f'Validating all variants in {self.file_accession}...')
        spdis = []
        skipped_spdis = []

        with gzip.open(self.filepath, 'rt') as sge_file:
            reader = csv.reader(sge_file, delimiter='\t')
            next(reader)
            for row in reader:
                spdi_chrom = CHR_MAP['GRCh38'].get(row[0])
                spdi = ':'.join(
                    [spdi_chrom, str(int(row[1])-1), row[2], row[3]])
                spdis.append(spdi)

        loaded_spdis = bulk_check_spdis_in_arangodb(spdis)
        for i, spdi in enumerate(spdis):
            if spdi not in loaded_spdis:
                print(f'Skipping {spdi} in row {str(i)}')
                skipped_spdis.append(spdi)
        print(f'{len(loaded_spdis)} out of {len(spdis)} variants are already loaded.')
        return skipped_spdis

    def validate_coding_variant(self, row, spdi, protein_id=None, splice=False):
        query_url = f'https://api-dev.catalog.igvf.org/api/variants/coding-variants?spdi={spdi}'
        coding_variant_key = []
        try:
            responses = requests.get(query_url).json()
            if not splice:
                ENSP_id, hgvsp = row[12].split(':')
                ENSP_id = ENSP_id.split('.')[0]
                for r in responses:
                    if r['protein_id'] == ENSP_id:
                        # double check if hgvsp is the same as loaded from dbNSFP
                        if r['hgvsp'] == hgvsp.replace('Ter', '*'):
                            coding_variant_key.append(r['_id'])
            else:
                for r in responses:
                    if r['protein_id'] == protein_id:
                        # hgvsp is null, no need to check that field
                        coding_variant_key.append(r['_id'])
            if len(coding_variant_key) > 1:
                print(
                    f"Warning: {spdi} has multiple mappings to {row[12]}, {', '.join(coding_variant_key)}")
            if len(coding_variant_key) == 0:
                print(f'Error: No coding variant mapping to {spdi}')
                return coding_variant_key
        except Exception as e:
            print(f'Error: {e}')
        return coding_variant_key[0]

    def load_splice_variants_hyperedge(self, protein_id, rows, edge_key):
        for row in rows:
            spdi_chrom = CHR_MAP['GRCh38'].get(row[0])
            spdi = ':'.join(
                [spdi_chrom, str(int(row[1])-1), row[2], row[3]])
            coding_variant_key = self.validate_coding_variant(
                row, spdi, protein_id, splice=True)

            if not coding_variant_key:
                print(
                    f'Skipping coding variant edge to {spdi}')
                continue
            else:
                hyperedge_key = '_'.join(
                    [spdi, self.PHENOTYPE_TERM, self.file_accession, coding_variant_key])
                _props = {
                    '_key': hyperedge_key,
                    '_from': 'variants_phenotypes/' + edge_key,
                    '_to': 'coding_variants/' + coding_variant_key,
                    'source': self.SOURCE,
                    'source_url': self.source_url,
                    'files_filesets': 'files_filesets/' + self.file_accession
                }
                self.writer.write(json.dumps(_props))
                self.writer.write('\n')

    def process_file(self):
        self.writer.open()
        # check if all variants in file is already loaded
        skipped_spdis = self.validate_variants()
        invalid_variants = []
        for spdi in skipped_spdis:
            variant_props, skipped = load_variant(spdi)
            if variant_props:
                variant_props.update({
                    'source': self.SOURCE,
                    'source_url': self.source_url,
                    'files_filesets': 'files_filesets/' + self.file_accession
                })
                if self.label == 'variants':
                    self.writer.write(json.dumps(variant_props))
                    self.writer.write('\n')
            elif skipped:
                print(
                    f"Invalid variant: {skipped['variant_id']} - {skipped['reason']}")
                invalid_variants.append(skipped['variant_id'])

        print(f'Skipping {len(invalid_variants)} invalid variants.')
        if self.label == 'variants':
            self.writer.close()
            return
        else:
            splice_variant_rows = []
            protein_id = ''
            with gzip.open(self.filepath, 'rt') as sge_file:
                reader = csv.reader(sge_file, delimiter='\t')
                headers = next(reader)
                for row in reader:
                    spdi_chrom = CHR_MAP['GRCh38'].get(row[0])
                    spdi = ':'.join(
                        [spdi_chrom, str(int(row[1])-1), row[2], row[3]])
                    # only skip invalid variants - new variants loaded from this adapter will be included
                    if spdi not in invalid_variants:
                        edge_key = spdi + '_' + self.PHENOTYPE_TERM + '_' + self.file_accession
                        if self.label == 'variants_phenotypes':
                            _props = {
                                '_key': edge_key,
                                '_from': 'variants/' + spdi,
                                '_to': 'ontology_terms/' + self.PHENOTYPE_TERM,
                                'source': self.SOURCE,
                                'source_url': self.source_url,
                                'files_filesets': 'files_filesets/' + self.file_accession
                            }

                            for column_index, field in enumerate(headers):
                                # don't need first 4 columns
                                if column_index > 3:
                                    prop = {}
                                    value = row[column_index]
                                    if field in self.FLOAT_FIELDS:
                                        prop[field] = float(
                                            value) if value != '' else None
                                    # starting from column 17 are integers
                                    elif column_index > 15:
                                        prop[field] = int(
                                            value) if value != '' else None
                                    else:
                                        prop[field] = value if value != '' and value != '---' else None

                                    _props.update(prop)

                            self.writer.write(json.dumps(_props))
                            self.writer.write('\n')
                        elif self.label == 'variants_phenotypes_coding_variants':
                            # exclude splice_site_variant in first round, run them seperately at the end, so ENSP id can be read from other rows in hgvsp column
                            # all rows in a single file should have the same ENSP id
                            # available hgvsp mapping in column 13, excluding synonymous change like ENSP00000261584.4:p.Arg1117=
                            if row[12] and '=' not in row[12] and row[6] != 'synonymous_variant':
                                if not protein_id:
                                    protein_id = row[12].split(
                                        ':')[0].split('.')[0]
                                continue
                                coding_variant_key = self.validate_coding_variant(
                                    row, spdi)
                                if not coding_variant_key:
                                    print(
                                        f'Skipping coding variant edge to {row[12]}')
                                    continue
                                else:
                                    hyperedge_key = '_'.join(
                                        [spdi, self.PHENOTYPE_TERM, self.file_accession, coding_variant_key])
                                    _props = {
                                        '_key': hyperedge_key,
                                        '_from': 'variants_phenotypes/' + edge_key,
                                        '_to': 'coding_variants/' + coding_variant_key,
                                        'source': self.SOURCE,
                                        'source_url': self.source_url,
                                        'files_filesets': 'files_filesets/' + self.file_accession
                                    }
                                    self.writer.write(json.dumps(_props))
                                    self.writer.write('\n')
                            elif row[6] == 'splice_site_variant':
                                splice_variant_rows.append(row)
            if self.label == 'variants_phenotypes_coding_variants':
                print(
                    f'Loading hyperedges to {len(splice_variant_rows)} splice variants...')
                self.load_splice_variants_hyperedge(
                    protein_id, splice_variant_rows, edge_key)
            self.writer.close()
