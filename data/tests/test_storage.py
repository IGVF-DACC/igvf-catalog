from unittest.mock import patch, Mock
from db.arango_db import ArangoDB
from adapters.storage import Storage

import pytest


def test_storage_raises_exception_if_schema_not_found():
    with pytest.raises(ValueError, match='Collection: random-collection not defined in registry.json'):
        Storage('random-collection')


def test_storage_ingests_registry_file_for_nodes():
    storage = Storage('genes')

    assert storage.element_type == 'node'
    assert storage.collection_name == 'genes'
    assert storage.db == 'arangodb'
    assert storage.dry_run == True


def test_storage_ingests_registry_file_for_edges():
    storage = Storage('genes_genes', db='clickhouse')

    assert storage.element_type == 'edge'
    assert storage.collection_name == 'genes_genes'
    assert storage.db == 'clickhouse'
    assert storage.dry_run == True


def test_storage_raises_exception_unsupported_db():
    with pytest.raises(ValueError, match='Supported database engines: \\[arangodb, clickhouse\\]'):
        Storage('genes_genes', db='mydb')


@patch('adapters.storage.ArangoDB')
def test_storage_saves_to_arango_dry_run(mock_arango, capsys):
    dummy_arangoimp = 'arangoimp <custom params>'
    mock_instance = Mock()
    mock_arango.return_value = mock_instance
    mock_instance.generate_json_import_statement.return_value = [
        dummy_arangoimp]

    storage = Storage('genes')
    storage.save_to_arango('./parsed-files/genes.jsonl', keep_file=True)

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
    storage.save_to_arango('./parsed-files/genes.jsonl', keep_file=True)

    args, kwargs = mock_instance.generate_json_import_statement.call_args
    assert args == ('./parsed-files/genes.jsonl', 'genes')
    assert kwargs == {'type': 'node'}

    mock_os.assert_called_with(dummy_arangoimp)


def test_storage_fetches_all_collections():
    collections = Storage.all_collections()
    # Check that we get a list with multiple collections from the real registry.json
    assert isinstance(collections, list)
    assert len(collections) > 0
    # Verify some expected collections are present
    assert 'genes' in collections
    assert 'genes_genes' in collections


@patch('os.remove')
@patch('adapters.storage.ArangoDB')
def test_storage_saves_to_arango_removes_file(mock_arango, mock_remove, capsys):
    dummy_arangoimp = 'arangoimp <custom params>'
    mock_instance = Mock()
    mock_arango.return_value = mock_instance
    mock_instance.generate_json_import_statement.return_value = [
        dummy_arangoimp]

    storage = Storage('genes')
    storage.save_to_arango('./parsed-files/genes.jsonl', keep_file=False)

    mock_remove.assert_called_with('./parsed-files/genes.jsonl')


@patch('adapters.storage.ArangoDB')
def test_storage_save_calls_arango(mock_arango, capsys):
    dummy_arangoimp = 'arangoimp <custom params>'
    mock_instance = Mock()
    mock_arango.return_value = mock_instance
    mock_instance.generate_json_import_statement.return_value = [
        dummy_arangoimp]

    storage = Storage('genes')
    storage.save('./parsed-files/genes.jsonl', keep_file=True)

    mock_instance.generate_json_import_statement.assert_called_once()


@patch('adapters.storage.Clickhouse')
def test_storage_save_calls_clickhouse(mock_clickhouse, capsys):
    dummy_cmd = 'clickhouse import command'
    mock_instance = Mock()
    mock_clickhouse.return_value = mock_instance
    mock_instance.generate_json_import_statement.return_value = dummy_cmd

    storage = Storage('genes_genes', db='clickhouse')
    storage.save('./parsed-files/genes_genes.jsonl', keep_file=True)

    mock_instance.generate_json_import_statement.assert_called_with(
        './parsed-files/genes_genes.jsonl', 'genes_genes')


@patch('os.remove')
@patch('adapters.storage.Clickhouse')
def test_storage_saves_to_clickhouse_dry_run(mock_clickhouse, mock_remove, capsys):
    dummy_cmd = 'clickhouse import command'
    mock_instance = Mock()
    mock_clickhouse.return_value = mock_instance
    mock_instance.generate_json_import_statement.return_value = dummy_cmd

    storage = Storage('genes_genes', db='clickhouse', dry_run=True)
    storage.save_to_clickhouse(
        './parsed-files/genes_genes.jsonl', keep_file=False)

    captured = capsys.readouterr()
    assert captured.out.strip() == dummy_cmd
    mock_remove.assert_called_with('./parsed-files/genes_genes.jsonl')


@patch('os.remove')
@patch('adapters.storage.Clickhouse')
def test_storage_saves_to_clickhouse_no_dry_run(mock_clickhouse, mock_remove):
    mock_instance = Mock()
    mock_clickhouse.return_value = mock_instance

    storage = Storage('genes_genes', db='clickhouse', dry_run=False)
    storage.save_to_clickhouse(
        './parsed-files/genes_genes.jsonl', keep_file=False)

    mock_instance.import_jsonl_file.assert_called_with(
        './parsed-files/genes_genes.jsonl', 'genes_genes')
    mock_remove.assert_called_with('./parsed-files/genes_genes.jsonl')
