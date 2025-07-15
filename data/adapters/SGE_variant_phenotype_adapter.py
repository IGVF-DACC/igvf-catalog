import csv
import json
import os
import gzip
from adapters.helpers import bulk_check_spdis_in_arangodb, CHR_MAP
from typing import Optional

from adapters.writer import Writer

# Example rows from SGE file (IGVFFI9974PZRX.tsv.gz)
# chrom	pos	ref	alt	exon	target	consequence	score	standard_error	95_ci_upper	95_ci_lower	amino_acid_change	hgvs_p	functional_consequence	functional_consequence_zscore	variant_qc_flag	snvlib_lib1	snvlib_lib2	D05_R1_lib1	D05_R1_lib2	D05_R2_lib1	D05_R2_lib2	D05_R3_lib1	D05_R3_lib2	D13_R1_lib1	D13_R1_lib2	D13_R2_lib1	D13_R2_lib2	D13_R3_lib1	D13_R3_lib2
# chr16	23603562	G	A	PALB2_X13	PALB2_X13A	missense_variant	-0.140561	0.0469519	-0.0485354	-0.232587	P1153L	ENSP00000261584.4:p.Pro1153Leu	functionally_abnormal	-4.24559	PASS	1155		114		326		361		158		297		512


class SGE:
    ALLOWED_LABELS = ['variants_phenotypes',
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
        print(f'{len(loaded_spdis)} out of {len(spdis)} variants are validated.')
        return skipped_spdis

    def process_file(self):
        self.writer.open()
        # check if all variants in file is already loaded
        skipped_spdis = self.validate_variants()

        with gzip.open(self.filepath, 'rt') as sge_file:
            reader = csv.reader(sge_file, delimiter='\t')
            headers = next(reader)
            # for idx, column_name in enumerate(headers):
            for row in reader:
                spdi_chrom = CHR_MAP['GRCh38'].get(row[0])
                spdi = ':'.join(
                    [spdi_chrom, str(int(row[1])-1), row[2], row[3]])
                # TODO: need to add load for those intron/UTR variants
                if spdi not in skipped_spdis:
                    edge_key = spdi + '_' + self.PHENOTYPE_TERM + '_' + self.file_accession

                    _props = {
                        '_key': edge_key,
                        'source': 'IGVF',
                        'source_url': self.source_url,
                        'files_filesets': 'files_filesets/' + self.file_accession
                    }

                    for column_index, field in enumerate(headers):
                        # don't need first 4 columns
                        if column_index > 3:
                            prop = {}
                            value = row[column_index]
                            prop[field] = value
                            if field in self.FLOAT_FIELDS:
                                prop[field] = float(
                                    value) if value != '' else None
                            # starting from column 17 are integers
                            if column_index > 15:
                                prop[field] = int(
                                    value) if value != '' else None
                            _props.update(prop)

                    self.writer.write(json.dumps(_props))
                    self.writer.write('\n')
        self.writer.close()
