from adapters import Adapter, OUTPUT_PATH
from unittest.mock import patch, mock_open, Mock
import yaml

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


@patch('builtins.open', new_callable=mock_open, read_data=MOCK_TEST_NODE)
def test_adapter_ingests_config_file_for_nodes(mock_op):
    class TestAdapter(Adapter):
        def __init__(self):
            self.label = 'test node'

            super(TestAdapter, self).__init__()

    adapter = TestAdapter()

    assert adapter.schema_config_name == 'test gene'
    assert adapter.schema_config == yaml.safe_load(MOCK_TEST_NODE)['test gene']
    assert adapter.element_type == 'node'
    assert adapter.file_prefix == 'TestGene'


@patch('builtins.open', new_callable=mock_open, read_data=MOCK_TEST_EDGE)
def test_adapter_ingests_config_file_for_edges(mock_op):
    class TestAdapter(Adapter):
        def __init__(self):
            self.label = 'test edge'

            super(TestAdapter, self).__init__()

    adapter = TestAdapter()

    assert adapter.schema_config_name == 'test correlation'
    assert adapter.schema_config == yaml.safe_load(MOCK_TEST_EDGE)[
        'test correlation']
    assert adapter.element_type == 'edge'
    assert adapter.file_prefix == 'CORRELATION'


@patch('adapters.ArangoDB')
@patch('builtins.open', new_callable=mock_open, read_data=MOCK_TEST_NODE)
def test_adapter_generate_arangodb_import_sts_per_chr(mock_op, mock_arango):
    with patch('glob.glob', return_value=['file1', 'file2']) as mock_glob:
        class TestAdapter(Adapter):
            def __init__(self):
                self.label = 'test node'
                self.file_prefix = 'test_prefix'
                self.chr = 'chr1'

                super(TestAdapter, self).__init__()

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


@patch('adapters.ArangoDB')
@patch('builtins.open', new_callable=mock_open, read_data=MOCK_TEST_EDGE)
def test_adapter_generate_arangodb_import_sts(mock_op, mock_arango):
    with patch('glob.glob', return_value=['file1', 'file2']) as mock_glob:
        class TestAdapter(Adapter):
            def __init__(self):
                self.label = 'test edge'
                self.file_prefix = 'test_prefix'

                super(TestAdapter, self).__init__()

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


@patch('builtins.open', new_callable=mock_open, read_data=MOCK_TEST_NODE)
def test_adapter_has_indexes(mock_op):
    class TestAdapter(Adapter):
        def __init__(self):
            self.label = 'test node'
            super(TestAdapter, self).__init__()

    adapter = TestAdapter()

    assert adapter.has_indexes() == True


@patch('builtins.open', new_callable=mock_open, read_data=MOCK_TEST_EDGE)
def test_adapter_doesnt_have_indexes(mock_op):
    class TestAdapter(Adapter):
        def __init__(self):
            self.label = 'test edge'
            super(TestAdapter, self).__init__()

    adapter = TestAdapter()

    assert adapter.has_indexes() == False


@patch('builtins.open', new_callable=mock_open, read_data=MOCK_TEST_EDGE)
def test_adapter_doesnt_create_indexes_if_not_set(mock_op, capfd):
    class TestAdapter(Adapter):
        def __init__(self):
            self.label = 'test edge'
            super(TestAdapter, self).__init__()

    adapter = TestAdapter()

    adapter.create_indexes()

    out, err = capfd.readouterr()

    assert out == 'No indexes registered in {} config\n'.format(
        adapter.collection)


@patch('adapters.ArangoDB')
@patch('builtins.open', new_callable=mock_open, read_data=MOCK_TEST_NODE)
def test_adapter_creates_indexes(mock_op, mock_arango):
    with patch('glob.glob', return_value=['file1', 'file2']) as mock_glob:
        class TestAdapter(Adapter):
            def __init__(self):
                self.label = 'test node'
                super(TestAdapter, self).__init__()

        adapter = TestAdapter()

        indexes = adapter.schema_config['db_indexes']
        index = [*indexes.keys()][0]

        adapter.create_indexes()

        mock_arango().create_index.assert_called_with(
            adapter.collection,
            indexes[index]['type'],
            indexes[index]['fields']
        )
