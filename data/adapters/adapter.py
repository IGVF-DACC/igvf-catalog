import biocypher
import yaml
import glob

BIOCYPHER_CONFIG_PATH = './schema-config.yaml'
BIOCYPHER_OUTPUT_PATH = './parsed-data/'


class Adapter:
  __biocypher_d = biocypher.Driver(
      offline=True,
      user_schema_config_path=BIOCYPHER_CONFIG_PATH,
      clear_cache=True,
      delimiter=',',
      output_directory=BIOCYPHER_OUTPUT_PATH
    )

  def __init__(self):
    with open(BIOCYPHER_CONFIG_PATH, 'r') as config:
      schema_configs = yaml.safe_load(config)

      for c in schema_configs:
        if schema_configs[c].get('label_in_input') == self.dataset:
          self.schema_config_name = c
          self.schema_config = schema_configs[c]
          break

    if self.schema_config['represented_as'] == 'edge':
      self.file_prefix = self.schema_config['label_as_edge']
      self.element_type = 'edge'
    else:
      self.file_prefix = ''.join(x for x in self.schema_config_name.title() if not x.isspace()) 
      self.element_type = 'node'


  @classmethod
  def get_biocypher(cls):
    return Adapter.__biocypher_d


  def print_ontology(self):
    Adapter.get_biocypher().show_ontology_structure()


  def write_file(self):
    if self.element_type == 'edge':
      Adapter.get_biocypher().write_edges(self.process_file())
    elif self.element_type == 'node':
      Adapter.get_biocypher().write_nodes(self.process_file())
    else:
      print('Unsuported element type')


  def arangodb(self):
    # header filename format: {label_as_edge}-header.csv
    header = self.file_prefix + '-header.csv'
    header_path = BIOCYPHER_OUTPUT_PATH + header

    # data filename format: {label_as_edge}_part{000 - *}.csv
    data_filenames = sorted(glob.glob(BIOCYPHER_OUTPUT_PATH + self.file_prefix + '-part*'))
    data_filepath = data_filenames[-1]

    collection = self.schema_config['db_collection_name']
    if self.schema_config['db_collection_per_chromosome']:
      collection += '_chr' + self.chr

    cmds = []
    for data_filepath in data_filenames:
      cmd = 'arangoimp --headers-file {} --file {} --type csv --collection {} --create-collection --remove-attribute ":TYPE" '.format(header_path, data_filepath, collection)
      if self.element_type == 'edge':
        cmd += '--create-collection-type edge --translate ":START_ID=_from" --translate ":END_ID=_to"'
      cmds.append(cmd)

    return cmds

