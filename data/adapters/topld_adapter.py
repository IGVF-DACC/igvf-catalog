import csv

from adapters import Adapter

# Example TOPLD input file:
# variant_1,variant_2,Uniq_ID_1,Uniq_ID_2,R2,Dprime,+/-corr
# 2781514,2781857,2781514:C:A,2781857:C:CT,0.233,0.809,+


class TopLD(Adapter):
    DATASET = 'topld'

    def __init__(self, filepath=None, chr='all', ancestry='SAS'):
        self.filepath = filepath
        self.chr = chr
        self.ancestry = ancestry
        self.dataset = TopLD.DATASET

        super(TopLD, self).__init__()

    def process_file(self):
        with open(self.filepath, 'r') as topld:
            topld_csv = csv.reader(topld)

            next(topld_csv)

            for row in topld_csv:
                try:
                    _id = row[2] + row[3]
                    _source = row[0]
                    _target = row[1]
                    label = 'topld'
                    _props = {
                        'chr': self.chr,
                        'negated': row[6] == '+',
                        'variant_1_base_pair': ':'.join(row[2].split(':')[1:3]),
                        'variant_2_base_pair': ':'.join(row[2].split(':')[1:3]),
                        'r2': row[4],
                        'd_prime': row[5],
                        'ancestry': self.ancestry
                    }

                    yield(_id, _source, _target, label, _props)
                except:
                    print(row)
                    pass
