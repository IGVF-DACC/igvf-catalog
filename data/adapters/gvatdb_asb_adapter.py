import csv
import pickle
from adapters import Adapter
from adapters.helpers import build_variant_id

# Example rows from GVATdb_hg38.csv: the tested variants are in the center position of the oligo
# The first three columns are variants coordinates in hg38,
# which are liftovered from the hg19 coordinates in the original file GVATdb.csv

# chr,start,end,TF,experiment,oligo,oligo_auc,oligo_pval,ref,alt,ref_auc,alt_auc,pbs,pval,fdr,rsid
# chr10,112626979,112626980,ALX1,FL.6.0.G12,chr10:114386719-114386759,3.02599,0.00133,C,T,1.44024,-1.28154,2.72179,0.31704,1,rs76124550


class ASB_GVATDB(Adapter):
    TF_ID_MAPPING_PATH = './data_loading_support_files/GVATdb_TF_mapping.pkl'
    SOURCE = 'GVATdb allele-specific TF binding calls'
    SOURCE_URL = 'https://renlab.sdsc.edu/GVATdb/'

    def __init__(self, filepath, label):
        self.filepath = filepath
        self.label = label

        super(ASB_GVATDB, self).__init__()

    def process_file(self):
        with open(self.filepath, 'r') as asb_file:
            asb_csv = csv.reader(asb_file)
            for row in asb_csv:
                chr = row[0]
                pos = row[2]  # 1-based coordinates
                ref = row[8]
                alt = row[9]

                variant_id = build_variant_id(
                    chr, pos, ref, alt, 'GRCh38'
                )

                tf_uniprot_id = self.tf_uniprot_id_mapping.get(row[3])
                if tf_uniprot_id is None:
                    continue

                # create separate edges for same variant-tf pairs in different experiments
                # or combine to the same edge? _key =  _key + '_' + row[4].replace('.','_')
                _id = variant_id + '_' + tf_uniprot_id
                _source = 'variants/' + variant_id
                _target = 'proteins/' + tf_uniprot_id

                _props = {
                    'source': ASB_GVATDB.SOURCE,
                    'source_url': ASB_GVATDB.SOURCE_URL
                }

                yield(_id, _source, _target, self.label, _props)

    def tf_uniprot_id_mapping(self):
        # map tf names to uniprot ids
        self.tf_uniprot_id_mapping = {}
        with open(ASB_GVATDB.TF_ID_MAPPING_PATH, 'rb') as tf_uniprot_id_mapfile:
            self.tf_uniprot_id_mapping = pickle.load(tf_uniprot_id_mapfile)
