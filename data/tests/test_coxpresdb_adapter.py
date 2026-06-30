import json
import pickle
from unittest.mock import patch
import pytest

from adapters.coxpresdb_adapter import Coxpresdb
from adapters.writer import SpyWriter


def mock_get(mock_request):
    mock_request.return_value.json.return_value = {
        'catalog_class': 'observed data',
        'catalog_method': 'COXPRESdb'
    }


def mock_entrez_gene_map():
    with open('./data_loading_support_files/entrez_to_ensembl.pkl', 'rb') as f:
        entrez_ensembl_dict = pickle.load(f)
    return {
        f'ENTREZ:{entrez_id}': [ensembl_id]
        for entrez_id, ensembl_id in entrez_ensembl_dict.items()
    }


@patch('adapters.coxpresdb_adapter.get_gene_map_from_arangodb')
@patch('adapters.coxpresdb_adapter.requests.get')
def test_coxpresdb_adapter(mock_request, mock_gene_map):
    mock_gene_map.return_value = mock_entrez_gene_map()
    mock_get(mock_request)
    writer = SpyWriter()
    adapter = Coxpresdb(filepath='./samples/coxpresdb/',
                        writer=writer, validate=True)
    adapter.process_file()

    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])

    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'z_score' in first_item
    assert first_item['source'] == adapter.source
    assert first_item['source_url'] == 'https://coxpresdb.jp/'
    assert first_item['name'] == 'coexpressed with'
    assert first_item['inverse_name'] == 'coexpressed with'
    assert first_item['associated_process'] == 'ontology_terms/GO_0010467'
    assert first_item['class'] == 'observed data'
    assert first_item['method'] == 'COXPRESdb'
    assert first_item['label'] == adapter.collection_label


@patch('adapters.coxpresdb_adapter.get_gene_map_from_arangodb')
@patch('adapters.coxpresdb_adapter.requests.get')
def test_coxpresdb_adapter_z_score_filter(mock_request, mock_gene_map):
    mock_gene_map.return_value = mock_entrez_gene_map()
    mock_get(mock_request)
    writer = SpyWriter()
    adapter = Coxpresdb(filepath='./samples/coxpresdb/', writer=writer)
    adapter.process_file()

    for item in writer.contents:
        if item.startswith('{'):
            data = json.loads(item)
            assert abs(float(data['z_score'])) >= 3


@patch('adapters.coxpresdb_adapter.get_gene_map_from_arangodb')
@patch('adapters.coxpresdb_adapter.requests.get')
def test_coxpresdb_adapter_deduplicates_gene_pairs(mock_request, mock_gene_map):
    mock_gene_map.return_value = mock_entrez_gene_map()
    mock_get(mock_request)
    writer = SpyWriter()
    adapter = Coxpresdb(filepath='./samples/coxpresdb/', writer=writer)
    adapter.process_file()

    edges = [json.loads(item)
             for item in writer.contents if item.startswith('{')]
    entrez_pairs = set()
    for edge in edges:
        key_body = edge['_key'].removesuffix('_coxpresdb')
        if key_body.startswith('ENSG'):
            pair = tuple(sorted(
                [key_body.split('_')[0], key_body.split('_', 1)[1]],
                key=lambda ens: ens,
            ))
        else:
            entrez_a, entrez_b = key_body.split('_', 1)
            pair = tuple(sorted([entrez_a, entrez_b], key=int))
        assert pair not in entrez_pairs
        entrez_pairs.add(pair)
        assert edge['_key'].endswith('_coxpresdb')


def test_coxpresdb_adapter_initialization():
    adapter = Coxpresdb(filepath='foobarbaz')
    assert adapter.filepath == 'foobarbaz'
    assert adapter.label == 'coxpresdb'
    assert adapter.source == 'COXPRESdb'
    assert adapter.source_url == 'https://coxpresdb.jp/'


def test_coxpresdb_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = Coxpresdb(filepath='./samples/coxpresdb/',
                        writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
