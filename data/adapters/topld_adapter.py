import csv
import yaml

from adapters import Adapter

# Example TOPLD input file:
# SNP1,SNP2,Uniq_ID_1,Uniq_ID_2,R2,Dprime,+/-corr
# 2781514,2781857,2781514:C:A,2781857:C:CT,0.233,0.809,+


class TopLD(Adapter):
  DATASET = 'topld'

  def __init__(self, chr='all', filepath=None, dry_run=True):
    self.filepath = filepath
    self.chr = chr
    self.dry_run = dry_run
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
            'source': row[0],
            'target': row[1],
            'chr': '22',

            'negated': row[6] == '+',
            'snp_1_base_pair': ':'.join(row[2].split(':')[1:3]),
            'snp_2_base_pair': ':'.join(row[2].split(':')[1:3]),
            'r2': row[4],
            'd_prime': row[5],
            'ancestry': 'SAS'
          }

          yield(_id, _source, _target, label, _props)
        except:
          print(row)
          pass

if __name__ == "__main__":
  adapter = TopLD(filepath='./samples/topld_sample.csv', chr='22')
  adapter.print_ontology()
  adapter.write_file()
  print(adapter.arangodb())
