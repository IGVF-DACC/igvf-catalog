import csv
import pickle
from adapters import Adapter
from adapters.helpers import build_variant_id

# Example rows from GVATdb_hg38.csv: the tested variants are in the center position of the oligo
# The first three columns are variants coordinates in hg38,
# which are liftovered from the hg19 coordinates in the original file GVATdb.csv

# chr,start,end,rsid,ref,alt,TF,experiment,oligo,oligo_auc,oligo_pval,ref_auc,alt_auc,pbs,pval,fdr
# chr1,49979657,49979658,rs4582846,C,T,DMRTC2,FL.7.1.A7,chr1:50445310-50445350,2.80064,0.03285,0.33993,0.58504,-0.24511,0.88535,0.98584


class ASB_GVATDB(Adapter):
    TF_ID_MAPPING_PATH = './data_loading_support_files/GVATdb_TF_mapping.pkl'
    SOURCE = 'GVATdb allele-specific TF binding calls'
    SOURCE_URL = 'https://renlab.sdsc.edu/GVATdb/'
    PVAL_THRESHOLD = 0.01

    def __init__(self, filepath, label):
        self.filepath = filepath
        self.label = label

        super(ASB_GVATDB, self).__init__()

    def process_file(self):
        self.load_tf_uniprot_id_mapping()

        with open(self.filepath, 'r') as asb_file:
            asb_csv = csv.reader(asb_file)
            for row in asb_csv:
                chr = row[0]
                pos = row[2]  # 1-based coordinates
                rsid = row[3]
                ref = row[4]
                alt = row[5]
                pval = float(row[-2])

                variant_id = build_variant_id(
                    chr, pos, ref, alt, 'GRCh38'
                )

                tf_uniprot_id = self.tf_uniprot_id_mapping.get(row[6])
                if tf_uniprot_id is None or len(tf_uniprot_id) == 0:
                    continue

                if pval > ASB_GVATDB.PVAL_THRESHOLD:
                    continue
                # create separate edges for same variant-tf pairs in different experiments
                # or combine to the same edge? _key =  _key + '_' + row[7].replace('.','_')
                _id = variant_id + '_' + tf_uniprot_id[0]
                _source = 'variants/' + variant_id
                _target = 'proteins/' + tf_uniprot_id[0]

                _props = {
                    'rsid': rsid,
                    'pval': pval,
                    'source': ASB_GVATDB.SOURCE,
                    'source_url': ASB_GVATDB.SOURCE_URL
                }

                yield(_id, _source, _target, self.label, _props)

    def load_tf_uniprot_id_mapping(self):
        # map tf names to uniprot ids
        self.tf_uniprot_id_mapping = {}
        with open(ASB_GVATDB.TF_ID_MAPPING_PATH, 'rb') as tf_uniprot_id_mapfile:
            self.tf_uniprot_id_mapping = pickle.load(tf_uniprot_id_mapfile)
