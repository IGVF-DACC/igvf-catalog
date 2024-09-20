from unittest.mock import patch, Mock
from db.arango_db import ArangoDB
from adapters.storage import Storage

import pytest
import yaml

MOCK_TEST_NODE = '''
gene:
  represented_as: node
  label_in_input: test node
  db_collection_name: genes
  db_collection_per_chromosome: true
  db_indexes:
    chr_index:
      type: persistent
      fields:
        - chr
  accessible_via:
    fuzzy_text_search: description
    delimiter_text_search: description
  properties:
    name: str
    description: str
    chr: str
'''

MOCK_TEST_EDGE = '''
genes genes edge:
  represented_as: edge
  label_in_input: test edge
  label_as_edge: CORRELATION
  db_collection_name: genes_genes
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


def test_storage_raises_exception_if_schema_not_found(mock_node_config):
    try:
        Storage('random-collection')
    except ValueError as e:
        assert str(
            e) == 'Collection: random-collection not defined in schema-config.yaml'


def test_storage_ingests_schema_config_file_for_nodes(mock_node_config):
    storage = Storage('genes')

    assert storage.schema_config_name == 'gene'
    assert storage.schema_config == yaml.safe_load(MOCK_TEST_NODE)['gene']
    assert storage.element_type == 'node'
    assert storage.collection == 'genes'
    assert storage.db == 'arangodb'


def test_storage_ingests_schema_config_file_for_edges(mock_edge_config):
    storage = Storage('genes_genes', db='clickhouse')

    assert storage.schema_config_name == 'genes genes edge'
    assert storage.schema_config == yaml.safe_load(MOCK_TEST_EDGE)[
        'genes genes edge']
    assert storage.element_type == 'edge'
    assert storage.collection == 'genes_genes'
    assert storage.db == 'clickhouse'


def test_storage_raises_exception_unsupported_db(mock_edge_config):
    try:
        storage = Storage('genes_genes', db='mydb')
    except ValueError as e:
        assert str(e) == 'Supported database engines: [arangodb, clickhouse]'


@patch('adapters.storage.ArangoDB')
def test_storage_saves_to_arango_dry_run(mock_arango, capsys):
    dummy_arangoimp = 'arangoimp <custom params>'
    mock_instance = Mock()
    mock_arango.return_value = mock_instance
    mock_instance.generate_json_import_statement.return_value = [
        dummy_arangoimp]

    storage = Storage('genes')
    storage.save_to_arango('./parsed-files/genes.jsonl')

    args, kwargs = mock_instance.generate_json_import_statement.call_args
    assert args == ('./parsed-files/genes.jsonl', 'genes')
    assert kwargs == {'type': 'node'}

    captured = capsys.readouterr()
    assert captured.out.strip() == dummy_arangoimp


@patch('os.system')
@patch('adapters.storage.ArangoDB')
def test_storage_saves_to_arango_no_dry_run(mock_arango, mock_os):
    dummy_arangoimp = 'arangoimp <custom params>'
    mock_instance = Mock()
    mock_arango.return_value = mock_instance
    mock_instance.generate_json_import_statement.return_value = [
        dummy_arangoimp]

    storage = Storage('genes', dry_run=False)
    storage.save_to_arango('./parsed-files/genes.jsonl')

    args, kwargs = mock_instance.generate_json_import_statement.call_args
    assert args == ('./parsed-files/genes.jsonl', 'genes')
    assert kwargs == {'type': 'node'}

    mock_os.assert_called_with(dummy_arangoimp)


def test_storage_fetches_all_collections(mock_node_config):
    collections = Storage.all_collections()
    assert collections == ['genes']


def test_storage_doesnt_create_index_if_not_defined(mock_edge_config, capsys):
    storage = Storage('genes_genes')
    storage.create_indexes()

    captured = capsys.readouterr()
    assert captured.out.strip() == 'No indexes registered in genes_genes config'


@patch('adapters.storage.ArangoDB')
def test_storage_creates_arangodb_index_if_not_defined(mock_arango, mock_node_config, capsys):
    mock_instance = Mock()
    mock_arango.return_value = mock_instance

    storage = Storage('genes')
    storage.create_indexes()

    mock_instance.create_index.assert_called_with(
        'genes', 'persistent', ['chr'])


@patch('adapters.storage.ArangoDB')
def test_storage_doesnt_create_index_if_not_defined(mock_arango, mock_node_config, capsys):
    mock_instance = Mock()
    mock_arango.return_value = mock_instance

    storage = Storage('genes')
    storage.create_indexes()

    mock_instance.create_index.assert_called_with(
        'genes', 'persistent', ['chr'])


@patch('adapters.storage.ArangoDB')
def test_storage_creates_arangodb_aliases(mock_arango, mock_node_config, capsys):
    mock_instance = Mock()
    mock_arango.return_value = mock_instance

    storage = Storage('genes')
    storage.create_aliases_arango(
        'name', 'idx_name', 'text_stem_en', 'view_name')

    args, kwargs = mock_instance.create_index.call_args
    assert args == ('genes', 'inverted', ['name'])
    assert kwargs == {'name': 'idx_name', 'opts': {'analyzer': 'text_stem_en'}}

    mock_instance.create_view.assert_called_with(
        'view_name', 'search-alias', 'genes', 'idx_name')


def test_storage_creates_proper_aliases(mock_node_config, capsys):
    mock_arango = Mock()
    storage = Storage('genes')
    storage.create_aliases_arango = mock_arango
    storage.create_aliases()

    mock_arango.assert_any_call(
        'description', 'genes_fuzzy_search', 'text_en_no_stem', 'genes_fuzzy_search_alias')
    mock_arango.assert_any_call(
        'description', 'genes_delimiter_search', 'text_delimiter', 'genes_delimiter_search_alias')
