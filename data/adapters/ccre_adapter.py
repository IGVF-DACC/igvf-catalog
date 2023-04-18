import gzip
import csv
from adapters import Adapter

# cCRE,all input file has 10 columns: chromsome, start, end, ID, score (all 0), strand (NA), start, end, color, biochemical_activity
# There are 8 types of biochemical_activity:
# pELS - proximal Enhancer-ike signal
# CA → chromatin accessible
# dELS - distal Enhancer-like signal
# TF → TF binding
# CA-CTCF
# CA-TF
# CA-H3K4me3
# PLS

# Below is example data:
# chr1    10033   10250   EH38E2776516    0       .       10033   10250   255,167,0       pELS
# chr1    10385   10713   EH38E2776517    0       .       10385   10713   255,167,0       pELS
# chr1    16097   16381   EH38E3951272    0       .       16097   16381   0,176,240       CA-CTCF
# chr1    17343   17642   EH38E3951273    0       .       17343   17642   190,40,229      CA-TF
# chr1    29320   29517   EH38E3951274    0       .       29320   29517   6,218,147       CA


class CCRE(Adapter):
    DATASET = 'ENCODE_candidate_cis_regulatory_element'

    BIOCHEMICAL_DESCRIPTION = {
        'pELS': 'proximal Enhancer-like signal',
        'CA': 'chromatin accessible',
        'dELS': 'distal Enhancer-like signal',
        'TF': 'TF binding',
        'CA-CTCF': 'chromatin accessible + CTCF binding',
        'CA-TF': 'chromatin accessible + TF binding',
        'CA-H3K4me3': 'chromatin accessible + H3K4me3 high signal',
        'PLS': 'Promoter-like signal'
    }

    def __init__(self, filepath):
        self.filepath = filepath
        self.dataset = CCRE.DATASET

        super(CCRE, self).__init__()

    def process_file(self):
        with gzip.open(self.filepath, 'rt') as input_file:
            reader = csv.reader(input_file, delimiter='\t')
            label = 'ENCODE_candidate_cis_regulatory_element'

            for row in reader:
                try:
                    description = CCRE.BIOCHEMICAL_DESCRIPTION.get(row[9])
                    _id = row[3]
                    _props = {
                        'chr': row[0],
                        'start': row[1],
                        'end': row[2],
                        'biochemical_activity': row[9],
                        'biochemical_activity_description': description
                    }
                    yield(_id, label, _props)

                except:
                    print(f'fail to process: {row}')
                    pass
