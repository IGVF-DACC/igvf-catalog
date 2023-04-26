import csv

from adapters import Adapter
from adapters.helpers import build_variant_id

# Example TOPLD input data file:

# SNP1,SNP2,Uniq_ID_1,Uniq_ID_2,R2,Dprime,+/-corr
# 5031031,5032123,5031031:C:T,5032123:G:A,0.251,0.888,+
# 5031031,5063457,5031031:C:T,5063457:G:C,0.443,0.832,+

# Example TOPLD annotation file:

# Position,rsID,MAF,REF,ALT,Uniq_ID,VEP_ensembl_Gene_Name,VEP_ensembl_Consequence,CADD_phred,fathmm_XF_coding_or_noncoding,FANTOM5_enhancer_expressed_tissue_cell
# 5031031,rs1441313282,0.010486891385767793,C,T,5031031:C:T,FP565260.3|FP565260.3|FP565260.3|FP565260.3|FP565260.3,"intron_variant|intron_variant|intron_variant|intron_variant,NMD_transcript_variant|intron_variant",2.135,.,.


class TopLD(Adapter):
    DATASET = 'topld_linkage_disequilibrium'

    def __init__(self, chr, data_filepath, annotation_filepath, ancestry='SAS'):
        self.data_filepath = data_filepath
        self.annotations_filepath = annotation_filepath

        self.chr = chr
        self.ancestry = ancestry
        self.dataset = TopLD.DATASET

        super(TopLD, self).__init__()

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
        with open(self.data_filepath, 'r') as topld:
            topld_csv = csv.reader(topld)

            next(topld_csv)

            for row in topld_csv:
                try:
                    _id = row[2] + row[3]
                    _source = self.ids[row[0]]['variant_id']
                    _target = self.ids[row[1]]['variant_id']
                    label = 'topld_linkage_disequilibrium'
                    _props = {
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

                    yield(_id, _source, _target, label, _props)
                except:
                    print(row)
                    pass
