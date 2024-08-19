import csv
import json
import os
import pickle
from adapters import Adapter
from adapters.helpers import build_variant_id
from math import log10
from db.arango_db import ArangoDB
# Example rows from GVATdb_hg38.csv: the tested variants are in the center position of the oligo
# The first three columns are variants coordinates in hg38,
# which are liftovered from the hg19 coordinates in the original file GVATdb.csv
# chr,start,end,rsid,ref,alt,TF,experiment,oligo,oligo_auc,oligo_pval,ref_auc,alt_auc,pbs,pval,fdr
# chr1,49979657,49979658,rs4582846,C,T,DMRTC2,FL.7.1.A7,chr1:50445310-50445350,2.80064,0.03285,0.33993,0.58504,-0.24511,0.88535,0.98584

# GVATdb_hg38.novel_batch.csv has less columns compared to GVATdb.csv
# Example rows:
# chr,start,end,snp,ref,alt,TF,experiment,oligo_auc,oligo_pval,pbs,pval
# chr1,940255,940256,chr1_875636_C_T,C,T,ASCL1,novel_batch,4.21438970378755,0.000343998624005503,1.0421349006409,0.632781468874124


class ASB_GVATDB(Adapter):
    TF_ID_MAPPING_PATH = './data_loading_support_files/GVATdb_TF_mapping.pkl'
    SOURCE = 'GVATdb allele-specific TF binding calls'
    SOURCE_URL = 'https://renlab.sdsc.edu/GVATdb/'
    OUTPUT_PATH = './parsed-data'

    def __init__(self, filepath, label, dry_run=True):
        self.filepath = filepath
        self.label = label
        self.dataset = label
        self.dry_run = dry_run
        self.type = 'edge'
        self.output_filepath = '{}/{}.json'.format(
            self.OUTPUT_PATH,
            self.dataset
        )

        super(ASB_GVATDB, self).__init__()

    def process_file(self):
        parsed_data_file = open(self.output_filepath, 'w')
        self.load_tf_uniprot_id_mapping()

        with open(self.filepath, 'r') as asb_file:
            asb_csv = csv.reader(asb_file)
            next(asb_csv)
            for row in asb_csv:
                chr = row[0]
                pos = row[2]  # 1-based coordinates
                ref = row[4]
                alt = row[5]

                experiment = row[7]
                if experiment != 'novel_batch':
                    pvalue = float(row[-2])
                    # the snp is on the central position of the oligo
                    hg19_pos = (int(row[8].split(':')[1].split(
                        '-')[0]) + int(row[8].split(':')[1].split('-')[1]))/2
                    hg19_coordinate = row[8].split(
                        # 1-based coordinates
                        ':')[0] + '_' + str(int(hg19_pos))
                else:
                    pvalue = float(row[-1])
                    hg19_coordinate = '_'.join(row[3].split('_')[:2])

                if pvalue == 0:
                    log_pvalue = None
                else:
                    log_pvalue = -1 * log10(pvalue)

                variant_id = build_variant_id(
                    chr, pos, ref, alt, 'GRCh38'
                )

                tf_uniprot_id = self.tf_uniprot_id_mapping.get(row[6])
                if tf_uniprot_id is None or len(tf_uniprot_id) == 0:
                    continue

                # create separate edges for same variant-tf pairs in different experiments
                _id = variant_id + '_' + \
                    tf_uniprot_id[0] + '_' + experiment.replace('.', '_')
                _source = 'variants/' + variant_id
                _target = 'proteins/' + tf_uniprot_id[0]

                _props = {
                    '_key': _id,
                    '_from': _source,
                    '_to': _target,
                    'log10pvalue': log_pvalue,
                    'p_value': pvalue,
                    # keep the original coordinate in hg19 in case people want to trace back
                    'hg19_coordinate': hg19_coordinate,
                    'source': ASB_GVATDB.SOURCE,
                    'source_url': ASB_GVATDB.SOURCE_URL,
                    'label': 'allele-specific binding',
                    'name': 'modulates binding of',
                    'inverse_name': 'binding modulated by',
                    'biological_process': 'ontology_terms/GO_0051101'
                }

                json.dump(_props, parsed_data_file)
                parsed_data_file.write('\n')
        parsed_data_file.close()
        self.save_to_arango()

    def load_tf_uniprot_id_mapping(self):
        # map tf names to uniprot ids
        self.tf_uniprot_id_mapping = {}
        with open(ASB_GVATDB.TF_ID_MAPPING_PATH, 'rb') as tf_uniprot_id_mapfile:
            self.tf_uniprot_id_mapping = pickle.load(tf_uniprot_id_mapfile)

    def save_to_arango(self):
        if self.dry_run:
            print(self.arangodb()[0])
        else:
            os.system(self.arangodb()[0])

    def arangodb(self):
        return ArangoDB().generate_json_import_statement(self.output_filepath, self.collection, type=self.type)
