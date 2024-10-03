import pytest
import yaml
from adapters import Adapter, OUTPUT_PATH

MOCK_TEST_NODE = '''
test gene:
  represented_as: node
  label_in_input: test node
  db_collection_name: test_collection
  db_collection_per_chromosome: true
  db_indexes:
    chr_index:
      type: persistent
      fields:
        - chr
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


@pytest.fixture
def mock_node_config(mocker):
    return mocker.patch('builtins.open', mocker.mock_open(read_data=MOCK_TEST_NODE))


@pytest.fixture
def mock_edge_config(mocker):
    return mocker.patch('builtins.open', mocker.mock_open(read_data=MOCK_TEST_EDGE))


def test_adapter_ingests_config_file_for_nodes(mock_node_config):
    class TestAdapter(Adapter):
        def __init__(self):
            self.label = 'test node'
            super().__init__()

    adapter = TestAdapter()

    assert adapter.schema_config_name == 'test gene'
    assert adapter.schema_config == yaml.safe_load(MOCK_TEST_NODE)['test gene']
    assert adapter.element_type == 'node'
    assert adapter.file_prefix == 'TestGene'


def test_adapter_ingests_config_file_for_edges(mock_edge_config):
    class TestAdapter(Adapter):
        def __init__(self):
            self.label = 'test edge'
            super().__init__()

    adapter = TestAdapter()

    assert adapter.schema_config_name == 'test correlation'
    assert adapter.schema_config == yaml.safe_load(MOCK_TEST_EDGE)[
        'test correlation']
    assert adapter.element_type == 'edge'
    assert adapter.file_prefix == 'CORRELATION'


def test_adapter_generate_arangodb_import_sts_per_chr(mock_node_config, mocker):
    mock_arango = mocker.patch('adapters.ArangoDB')
    mock_glob = mocker.patch('glob.glob', return_value=['file1', 'file2'])

    class TestAdapter(Adapter):
        def __init__(self):
            self.label = 'test node'
            self.file_prefix = 'test_prefix'
            self.chr = 'chr1'
            super().__init__()

        def process_file(self):
            return 'Test file processed'

    adapter = TestAdapter()
    adapter.arangodb()

    mock_arango().generate_import_statement.assert_called_with(
        OUTPUT_PATH + adapter.file_prefix + '-header.csv',
        mock_glob.return_value,
        'test_collection_chr1',
        'node',
        True
    )


def test_adapter_generate_arangodb_import_sts(mock_edge_config, mocker):
    mock_arango = mocker.patch('adapters.ArangoDB')
    mock_glob = mocker.patch('glob.glob', return_value=['file1', 'file2'])

    class TestAdapter(Adapter):
        def __init__(self):
            self.label = 'test edge'
            self.file_prefix = 'test_prefix'
            super().__init__()

        def process_file(self):
            return 'Test file processed'

    adapter = TestAdapter()
    adapter.arangodb()

    mock_arango().generate_import_statement.assert_called_with(
        OUTPUT_PATH + adapter.file_prefix + '-header.csv',
        mock_glob.return_value,
        'test_collection_edges',
        'edge',
        True
    )


def test_adapter_has_indexes(mock_node_config):
    class TestAdapter(Adapter):
        def __init__(self):
            self.label = 'test node'
            super().__init__()

    adapter = TestAdapter()
    assert adapter.has_indexes() == True


def test_adapter_doesnt_have_indexes(mock_edge_config):
    class TestAdapter(Adapter):
        def __init__(self):
            self.label = 'test edge'
            super().__init__()

    adapter = TestAdapter()
    assert adapter.has_indexes() == False


def test_adapter_doesnt_create_indexes_if_not_set(mock_edge_config, capsys):
    class TestAdapter(Adapter):
        def __init__(self):
            self.label = 'test edge'
            super().__init__()

    adapter = TestAdapter()
    adapter.create_indexes()

    captured = capsys.readouterr()
    assert captured.out == f'No indexes registered in {
        adapter.collection} config\n'


def test_adapter_creates_indexes(mock_node_config, mocker):
    mock_arango = mocker.patch('adapters.ArangoDB')

    class TestAdapter(Adapter):
        def __init__(self):
            self.label = 'test node'
            super().__init__()

    adapter = TestAdapter()
    indexes = adapter.schema_config['db_indexes']
    index = next(iter(indexes))

    adapter.create_indexes()

    mock_arango().create_index.assert_called_with(
        adapter.collection,
        indexes[index]['type'],
        indexes[index]['fields']
    )
