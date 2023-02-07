from adapters import Adapter, BIOCYPHER_OUTPUT_PATH
from unittest.mock import patch, mock_open, Mock
import yaml
import biocypher


MOCK_TEST_NODE = '''
test gene:
  represented_as: node
  label_in_input: test node
  db_collection_name: test_collection
  db_collection_per_chromosome: true
  properties:
    name: str
    description: str
    chr: str
'''


MOCK_TEST_EDGE = '''
test correlation:
  represented_as: edge
  label_in_input: test edge
  label_as_edge: CORRELATION
  db_collection_name: test_collection_edges
  db_collection_per_chromosome: false
  properties:
    source: str
    target: str
    chr: str
'''


@patch("builtins.open", new_callable=mock_open, read_data=MOCK_TEST_NODE)
def test_adapter_ingests_config_file_for_nodes(mock_op):
  class TestAdapter(Adapter):
    def __init__(self):
      self.dataset = 'test node'

      super(TestAdapter, self).__init__()

  
  adapter = TestAdapter()

  assert adapter.schema_config_name == 'test gene'
  assert adapter.schema_config == yaml.safe_load(MOCK_TEST_NODE)['test gene']
  assert adapter.element_type == 'node'
  assert adapter.file_prefix == 'TestGene'


@patch("builtins.open", new_callable=mock_open, read_data=MOCK_TEST_EDGE)
def test_adapter_ingests_config_file_for_edges(mock_op):
  class TestAdapter(Adapter):
    def __init__(self):
      self.dataset = 'test edge'

      super(TestAdapter, self).__init__()

  
  adapter = TestAdapter()

  assert adapter.schema_config_name == 'test correlation'
  assert adapter.schema_config == yaml.safe_load(MOCK_TEST_EDGE)['test correlation']
  assert adapter.element_type == 'edge'
  assert adapter.file_prefix == 'CORRELATION'


def test_adapter_creates_biocypher_connection():
  class TestAdapter(Adapter):
    def __init__(self):
      self.dataset = 'test edge'

      super(TestAdapter, self).__init__()

  assert isinstance(Adapter.get_biocypher(), biocypher._driver.Driver)


@patch("builtins.open", new_callable=mock_open, read_data=MOCK_TEST_EDGE)
def test_adapter_prints_ontology(mock_op): 
  mock_bio = Mock()

  with patch("adapters.Adapter.get_biocypher", return_value=mock_bio) as mock_driver:
    class TestAdapter(Adapter):
      def __init__(self):
        self.dataset = 'test edge'

        super(TestAdapter, self).__init__()

    adapter= TestAdapter()

    adapter.print_ontology()

    mock_bio.show_ontology_structure.assert_called_once()


@patch("builtins.open", new_callable=mock_open, read_data=MOCK_TEST_EDGE)
def test_adapter_writes_edges(mock_op):
  mock_bio = Mock()

  with patch("adapters.Adapter.get_biocypher", return_value=mock_bio) as mock_driver:
    class TestAdapter(Adapter):
      def __init__(self):
        self.dataset = 'test edge'

        super(TestAdapter, self).__init__()

      def process_file(self):
        return "Test file processed"

    adapter= TestAdapter()

    adapter.write_file()

    mock_bio.write_edges.assert_called_with("Test file processed")


@patch("builtins.open", new_callable=mock_open, read_data=MOCK_TEST_NODE)
def test_adapter_writes_nodes(mock_op):
  mock_bio = Mock()

  with patch("adapters.Adapter.get_biocypher", return_value=mock_bio) as mock_driver:
    class TestAdapter(Adapter):
      def __init__(self):
        self.dataset = 'test node'

        super(TestAdapter, self).__init__()

      def process_file(self):
        return "Test file processed"

    adapter= TestAdapter()

    adapter.write_file()

    mock_bio.write_nodes.assert_called_with("Test file processed")


@patch('adapters.ArangoDB')
@patch("builtins.open", new_callable=mock_open, read_data=MOCK_TEST_NODE)
def test_adapter_generate_arangodb_import_sts_per_chr(mock_op, mock_arango):
  with patch("glob.glob", return_value=['file1', 'file2']) as mock_glob:
    class TestAdapter(Adapter):
      def __init__(self):
        self.dataset = 'test node'
        self.file_prefix = 'test_prefix'
        self.chr = 'chr1'

        super(TestAdapter, self).__init__()

      def process_file(self):
        return "Test file processed"

    adapter= TestAdapter()

    adapter.arangodb()

    mock_arango().generate_import_statement.assert_called_with(
      BIOCYPHER_OUTPUT_PATH + adapter.file_prefix + '-header.csv',
      mock_glob.return_value,
      'test_collection_chr1',
      'node'
    )


@patch('adapters.ArangoDB')
@patch("builtins.open", new_callable=mock_open, read_data=MOCK_TEST_EDGE)
def test_adapter_generate_arangodb_import_sts(mock_op, mock_arango):
  with patch("glob.glob", return_value=['file1', 'file2']) as mock_glob:
    class TestAdapter(Adapter):
      def __init__(self):
        self.dataset = 'test edge'
        self.file_prefix = 'test_prefix'

        super(TestAdapter, self).__init__()

      def process_file(self):
        return "Test file processed"

    adapter= TestAdapter()

    adapter.arangodb()

    mock_arango().generate_import_statement.assert_called_with(
      BIOCYPHER_OUTPUT_PATH + adapter.file_prefix + '-header.csv',
      mock_glob.return_value,
      'test_collection_edges',
      'edge'
    )
