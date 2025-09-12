import json
from unittest.mock import MagicMock, patch
from adapters.oncotree_adapter import Oncotree
from adapters.writer import SpyWriter

SAMPLE_RESPONSE = [
    {
        'code': 'MDS/MPN',
        'name': 'Myelodysplastic/Myeloproliferative Neoplasm',
        'mainType': 'Myeloid Neoplasm',
        'externalReferences': {'NCI': ['C002'], 'UMLS': ['C123']},
        'tissue': 'Blood',
        'children': {},
        'parent': 'EMBT',
        'history': [],
        'level': 3,
        'revocations': [],
        'precursors': []
    },
    {
        'code': 'MMB',
        'name': 'Medullomyoblastoma',
        'mainType': 'Embryonal Tumor',
        'externalReferences': {},
        'tissue': 'CNS/Brain',
        'children': {},
        'parent': None,
        'history': [],
        'level': 3,
        'revocations': [],
        'precursors': []
    }
]


@patch('adapters.oncotree_adapter.requests.get')
def test_oncotree_adapter(mock_get):
    mock_get.return_value.json.return_value = SAMPLE_RESPONSE

    writer = SpyWriter()
    adapter = Oncotree(type='node', writer=writer)
    adapter.process_file()
    assert len(writer.contents) > 1
    first_item = json.loads(writer.contents[0])
    assert '_key' in first_item
    assert 'term_id' in first_item
    assert 'name' in first_item
    assert 'source' in first_item
    assert 'uri' in first_item
    assert first_item['source'] == 'Oncotree'


@patch('adapters.oncotree_adapter.requests.get')
def test_oncotree_adapter_edges(mock_get):
    mock_get.return_value.json.return_value = SAMPLE_RESPONSE

    writer = SpyWriter()
    adapter = Oncotree(type='edge', writer=writer)
    adapter.process_file()
    assert len(writer.contents) > 1
    first_item = json.loads(writer.contents[0])
    assert 'type' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['source'] == 'Oncotree'


@patch('adapters.oncotree_adapter.requests.get')
def test_process_file_writer_closed_on_finish(mock_get):
    mock_get.return_value.json.return_value = SAMPLE_RESPONSE
    writer = MagicMock()
    oncotree = Oncotree(type='node', writer=writer)
    oncotree.process_file()
    assert writer.close.called
