import biocypher

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
    pass

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
