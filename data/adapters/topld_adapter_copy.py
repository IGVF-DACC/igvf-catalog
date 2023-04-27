import csv
import json
import os
from db.arango_db import ArangoDB
from adapters import Adapter
from adapters.helpers import build_variant_id

# Example TOPLD input data file:

# SNP1,SNP2,Uniq_ID_1,Uniq_ID_2,R2,Dprime,+/-corr
# 5031031,5032123,5031031:C:T,5032123:G:A,0.251,0.888,+
# 5031031,5063457,5031031:C:T,5063457:G:C,0.443,0.832,+

# Example TOPLD annotation file:

# Position,rsID,MAF,REF,ALT,Uniq_ID,VEP_ensembl_Gene_Name,VEP_ensembl_Consequence,CADD_phred,fathmm_XF_coding_or_noncoding,FANTOM5_enhancer_expressed_tissue_cell
# 5031031,rs1441313282,0.010486891385767793,C,T,5031031:C:T,FP565260.3|FP565260.3|FP565260.3|FP565260.3|FP565260.3,"intron_variant|intron_variant|intron_variant|intron_variant,NMD_transcript_variant|intron_variant",2.135,.,.


class TopLD2(Adapter):
    DATASET = 'topld_linkage_disequilibrium'

    OUTPUT_PATH = './parsed-data'

    def __init__(self, chr, data_filepath, annotation_filepath, ancestry='SAS', dry_run=True):
        self.data_filepath = data_filepath
        self.annotations_filepath = annotation_filepath

        self.chr = chr
        self.ancestry = ancestry
        self.dataset = TopLD2.DATASET

        self.dry_run = dry_run

        self.output_filepath = '{}/{}-{}.json'.format(
            TopLD2.OUTPUT_PATH,
            self.dataset,
            data_filepath.split('/')[-1]
        )

        super(TopLD2, self).__init__()

    def process_annotations(self):
        print('Processing annotations...')
        self.ids = {}
        with open(self.annotations_filepath, 'r') as annotations:
            annotations_csv = csv.reader(annotations)

            next(annotations_csv)

            for row in annotations_csv:
                self.ids[row[0]] = {
                    'rsid': row[1],
                    'variant_id': 'variants/' + build_variant_id(
                        self.chr,
                        row[0],
                        row[3],
                        row[4]
                    )
                }

    def process_file(self):
        self.process_annotations()

        print('Processing data...')

        parsed_data_file = open(self.output_filepath, 'w')
        record_count = 0

        for line in open(self.data_filepath, 'r'):
            row = line.split(',')

            if row[0] == 'SNP1':
                continue

            id = row[2] + row[3]
            source = self.ids[row[0]]['variant_id']
            target = self.ids[row[1]]['variant_id']

            to_json = {
                '_key': id,
                '_from': source,
                '_to': target,
                'chr': self.chr,
                'negated': row[6] == '+',
                'variant_1_base_pair': ':'.join(row[2].split(':')[1:3]),
                'variant_2_base_pair': ':'.join(row[3].split(':')[1:3]),
                'variant_1_rsid': self.ids[row[0]]['rsid'],
                'variant_2_rsid': self.ids[row[1]]['rsid'],
                'r2': row[4],
                'd_prime': row[5],
                'ancestry': self.ancestry,
                'label': 'linkage disequilibrum',
                'source': 'TopLD',
                'source_url': 'http://topld.genetics.unc.edu/'
            }

            json.dump(to_json, parsed_data_file)
            parsed_data_file.write('\n')
            record_count += 1

            if record_count > 1000000:
                parsed_data_file.close()
                self.save_to_arango()

                os.remove(self.output_filepath)
                record_count = 0

                parsed_data_file = open(self.output_filepath, 'w')

        parsed_data_file.close()
        self.save_to_arango()

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection)

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
            import pdb
            pdb.set_trace()
        else:
            os.system(self.arangodb()[0])
