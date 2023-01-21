import csv
import yaml
import glob

from adapter import Adapter, BIOCYPHER_CONFIG_PATH, BIOCYPHER_OUTPUT_PATH

# Example TOPLD input file:
# SNP1,SNP2,Uniq_ID_1,Uniq_ID_2,R2,Dprime,+/-corr
# 2781514,2781857,2781514:C:A,2781857:C:CT,0.233,0.809,+

TOPLD_CONFIG_PATH = './data_config/topld_config.yaml'

class TopLD(Adapter):
  DATASET = 'topld'

  def __init__(self, chr='all', filepath=None, dry_run=True):
    self.filepath = filepath
    self.chr = chr
    self.dry_run = dry_run

    with open(TOPLD_CONFIG_PATH, 'r') as config:
      self.config = yaml.safe_load(config)[TopLD.DATASET]

    with open(BIOCYPHER_CONFIG_PATH, 'r') as config:
      self.biocypher_config = yaml.safe_load(config)[TopLD.DATASET]

    self.element_type = self.config['type']


  def arangodb(self):
    if self.element_type == 'edge':
      prefix = self.biocypher_config['label_as_edge']

    # header filename format: {label_as_edge}-header.csv
    header = prefix + '-header.csv'
    header_path = BIOCYPHER_OUTPUT_PATH + header

    # data filename format: {label_as_edge}_part{000 - *}.csv
    data_filenames = sorted(glob.glob(BIOCYPHER_OUTPUT_PATH + prefix + '-part*'))
    data_filepath = data_filenames[-1]

    collection = self.config['collection_name']
    if self.config['collection_per_chromosome']:
      collection += '_chr' + self.chr

    cmd = 'arangoimp --headers-file {} --file {} --type csv --collection {} --create-collection --remove-attribute ":TYPE" '.format(header_path, data_filepath, collection)
    if self.element_type == 'edge':
      cmd += '--create-collection-type edge --translate ":START_ID=_from" --translate ":END_ID=_to"'
    return cmd


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
  tld = TopLD(filepath='example_file', chr='22')
  tld.print_ontology()
  tld.write_file()
  print(tld.arangodb())


