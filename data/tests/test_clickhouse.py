import json
from unittest.mock import patch, mock_open, Mock, call

from db.clickhouse import Clickhouse, SCHEMA_REGISTRY_PATH, DB_CONFIG_PATH

MOCK_JSONL = '''{"_key": "gene_1", "name": "test gene 1", "description": "test description 1", "chr": "chr1"}
{"_key": "gene_2", "name": "test gene 2", "description": "test description 2", "chr": "chr1"}
{"_key": "gene_3", "name": "test gene 3", "description": "test description 3", "chr": "chr1"}
'''

MOCK_REGISTRY = '''{
    "nodes": {
        "genes": {
            "GencodeGene": "schemas/nodes/genes.GencodeGene.json"
        }
    },
    "edges": {
        "genes_genes": {
            "GeneGeneBiogrid": "schemas/edges/genes_genes.GeneGeneBiogrid.json"
        }
    }
}'''

MOCK_NODE_SCHEMA = {
    'properties': {
        'name': {'type': 'string'},
        'description': {'type': 'string'},
        'chr': {'type': 'string'}
    }
}

MOCK_EDGE_SCHEMA = {
    'properties': {
        'source': {'type': 'string'},
        'target': {'type': 'array'},
        'chr': {'type': 'object'},
        '_from': {
            'type': 'string',
            'collections': ['genes']
        },
        '_to': {
            'type': 'string',
            'collections': ['genes']
        }
    }
}

MOCK_CONFIG_FILE = '''
{
  "environment": "development",
  "host": {
    "protocol": "http",
    "hostname": "localhost",
    "port": 2023
  },
  "database": {
    "connectionUri": "http://example.org:8529",
    "dbName": "igvf",
    "auth": {
        "username": "test",
        "password": "test"
    }
  },
  "clickhouse": {
    "host": "localhost",
    "port": 9000,
    "dbName": "igvf-clickhouse",
    "auth": {
      "username": "default",
      "password": ""
    }
  }
}'''

schema_sql_file = mock_open()()


def filename_to_mock_open(filename: str, *args, **kwargs):
    return {
        SCHEMA_REGISTRY_PATH: mock_open(read_data=MOCK_REGISTRY)(),
        DB_CONFIG_PATH: mock_open(read_data=MOCK_CONFIG_FILE)(),
        'genes.jsonl': mock_open(read_data=MOCK_JSONL)(),
        'schema.sql': schema_sql_file
    }[filename]


def mock_open_multiple(on_open):
    mock_files = mock_open()
    mock_files.side_effect = on_open
    mock_files.return_value = None
    return mock_files


def get_schema_side_effect(collection_type, table_name, adapter_name):
    """Shared mock for get_schema that returns copies to avoid mutation issues"""
    if collection_type == 'edges':
        return json.loads(json.dumps(MOCK_EDGE_SCHEMA))
    return json.loads(json.dumps(MOCK_NODE_SCHEMA))


@patch('db.clickhouse.get_schema')
@patch('clickhouse_driver.Client')
def test_clickhouse_ingests_config_file(mock_client, mock_get_schema):
    mock_get_schema.side_effect = get_schema_side_effect
    m = mock_open_multiple(on_open=filename_to_mock_open)
    with patch('builtins.open', m):
        db = Clickhouse(reconnect=True)

        assert db.db_name == 'igvf-clickhouse'

        mock_client.assert_called_with(
            host='localhost',
            port=9000,
            database='igvf-clickhouse',
            user='default',
            password=''
        )


@patch('db.clickhouse.get_schema')
@patch('builtins.open', new_callable=mock_open, read_data=MOCK_REGISTRY)
def test_clickhouse_loads_schema(mock_open_file, mock_get_schema):
    mock_get_schema.side_effect = get_schema_side_effect
    schema = Clickhouse.load_schema()

    assert schema['genes'] == {
        'properties': {
            'name': 'string',
            'description': 'string',
            'chr': 'string'
        }
    }


@patch('db.clickhouse.get_schema')
@patch('builtins.open', new_callable=mock_open, read_data=MOCK_REGISTRY)
def test_clickhouse_loads_schema_with_relationship_schema(mock_open_file, mock_get_schema):
    mock_get_schema.side_effect = get_schema_side_effect
    schema = Clickhouse.load_schema()

    assert schema['genes_genes'] == {
        'properties': {
            'source': 'string',
            'target': 'array',
            'chr': 'object'
        },
        'relationship': {
            'from': ['genes_1_id'],
            'to': ['genes_2_id']
        }
    }


@patch('db.clickhouse.get_schema')
def test_clickhouse_processes_json_line_from_node(mock_get_schema):
    mock_get_schema.side_effect = get_schema_side_effect
    m = mock_open_multiple(on_open=filename_to_mock_open)
    with patch('builtins.open', m):
        clickhouse = Clickhouse()
        properties = Clickhouse.get_schema()['genes']['properties']
        test_json_line = json.dumps(
            {'_key': 'gene_id', 'name': 'test gene', 'description': 'test description', 'chr': 'chr1'})
        result = clickhouse.process_json_line(test_json_line, properties)
        assert result == ['test gene', 'test description', 'chr1', 'gene_id']


@patch('db.clickhouse.get_schema')
def test_clickhouse_processes_json_line_from_edge(mock_get_schema):
    mock_get_schema.side_effect = get_schema_side_effect
    m = mock_open_multiple(on_open=filename_to_mock_open)
    with patch('builtins.open', m):
        clickhouse = Clickhouse()
        properties = Clickhouse.get_schema()['genes_genes']['properties']
        test_json_line = json.dumps({'_key': 'gene_id', '_from': 'gene_1', '_to': 'gene_2',
                                    'source': 'test dataset', 'target': 'cell', 'chr': 'chr1'})
        result = clickhouse.process_json_line(test_json_line, properties)
        assert result == ['test dataset', 'cell',
                          'chr1', 'gene_id', 'gene_1', 'gene_2']


@patch('db.clickhouse.get_schema')
def test_clickhouse_raises_exception_if_imports_jsonl_file_for_inexistent_collection(mock_get_schema):
    mock_get_schema.return_value = MOCK_NODE_SCHEMA
    m = mock_open_multiple(on_open=filename_to_mock_open)
    with patch('builtins.open', m):
        clickhouse = Clickhouse()
        try:
            clickhouse.import_jsonl_file(
                'test_jsonl.json', 'inexistent collection')
        except Exception as e:
            assert str(e) == 'Collection not defined in schema registry'


@patch('db.clickhouse.get_schema')
def test_clickhouse_imports_jsonl_file(mock_get_schema):
    mock_get_schema.return_value = MOCK_NODE_SCHEMA
    m = mock_open_multiple(on_open=filename_to_mock_open)

    insert = [('test gene 1', 'test description 1', 'chr1', 'gene_1'), ('test gene 2',
                                                                        'test description 2', 'chr1', 'gene_2'), ('test gene 3', 'test description 3', 'chr1', 'gene_3')]

    with patch('clickhouse_driver.Client') as mock_client:
        connection = Mock()
        mock_client.return_value = connection

        with patch('builtins.open', m):
            Clickhouse(reconnect=True).import_jsonl_file(
                'genes.jsonl', 'genes')
            print(connection)
            connection.execute.assert_called_with(
                'INSERT INTO genes (name,description,chr,id) VALUES', insert)


@patch('db.clickhouse.get_schema')
def test_clickhouse_generates_sql_schema(mock_get_schema):
    mock_get_schema.side_effect = get_schema_side_effect

    write_mock = Mock()
    schema_sql_file.write = write_mock
    m = mock_open_multiple(on_open=filename_to_mock_open)

    with patch('builtins.open', m):
        clickhouse = Clickhouse()
        clickhouse.generate_sql_schema('schema.sql')

    assert call(
        '-- autogenerated from schema registry\n\n') in write_mock.call_args_list
    assert call(
        'SET allow_experimental_json_type = 1;\n\n') in write_mock.call_args_list
    assert call('USE igvf-clickhouse;\n\n') in write_mock.call_args_list
    assert call(
        '\nCREATE TABLE IF NOT EXISTS genes (\n\t') in write_mock.call_args_list
    assert call(
        'name String,\n\tdescription String,\n\tchr String,\n\tid String PRIMARY KEY') in write_mock.call_args_list
    assert call('\n);\n') in write_mock.call_args_list
    assert call(
        '\nCREATE TABLE IF NOT EXISTS genes_genes (\n\t') in write_mock.call_args_list
    assert call('source String,\n\ttarget Array(String),\n\tchr String,\n\tid String PRIMARY KEY,\n\tgenes_1_id String,\n\tgenes_2_id String') in write_mock.call_args_list
    assert call('\n);\n') in write_mock.call_args_list
