import json
import pytest
from unittest.mock import patch
from adapters.gaf_adapter import GAF
from adapters.writer import SpyWriter


@pytest.fixture(autouse=True)
def mock_file_fileset():
    with patch('adapters.gaf_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get:
        mock_get.return_value = {
            'class': 'biological relationship',
            'method': None
        }
        yield mock_get


@pytest.fixture
def mock_protein_map():
    with patch('adapters.gaf_adapter.get_protein_map_from_arangodb') as mock_get:
        mock_get.return_value = {
            'A0A024RBG1': ['ENSP00000263100'],
            'MGI:1915609': ['ENSMUSP00000000001'],
        }
        yield mock_get


def test_gaf_adapter_human(mock_file_fileset, mock_protein_map):
    writer = SpyWriter()
    adapter = GAF(filepath='./samples/goa_human_sample.gaf.gz',
                  label='human', writer=writer, validate=True)
    adapter.file_accession = 'IGVFFI1490WZCV'
    adapter.process_file()
    mock_file_fileset.assert_called_once_with('IGVFFI1490WZCV')
    mock_protein_map.assert_called_once_with(organism='Homo sapiens')
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_from'] == 'proteins/ENSP00000263100'
    assert '_to' in first_item
    assert first_item['organism'] == 'Homo sapiens'
    assert first_item['source'] == 'Gene Ontology'
    assert first_item['source_url'] == GAF.SOURCES['human']
    assert first_item['class'] == 'biological relationship'
    assert first_item['method'] is None
    assert first_item['label'] is None
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI1490WZCV'


def test_gaf_adapter_mouse(mock_file_fileset, mock_protein_map):
    writer = SpyWriter()
    adapter = GAF(filepath='./samples/mgi_sample.gaf.gz',
                  label='mouse', writer=writer, validate=True)
    adapter.file_accession = 'IGVFFI9807JOKT'
    adapter.process_file()
    mock_file_fileset.assert_called_once_with('IGVFFI9807JOKT')
    mock_protein_map.assert_called_once_with(
        dbxref_name='MGI', organism='Mus musculus')
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_from'] == 'proteins/ENSMUSP00000000001'
    assert '_to' in first_item
    assert first_item['organism'] == 'Mus musculus'
    assert first_item['source'] == 'Gene Ontology'
    assert first_item['source_url'] == GAF.SOURCES['mouse']
    assert first_item['class'] == 'biological relationship'
    assert first_item['method'] is None
    assert first_item['label'] is None
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI9807JOKT'


def test_gaf_adapter_rna(mock_file_fileset):
    writer = SpyWriter()
    adapter = GAF(filepath='./samples/goa_human_rna.gaf.gz',
                  label='rna', writer=writer, validate=True)
    adapter.file_accession = 'IGVFFI6501YXMX'
    adapter.process_file()
    mock_file_fileset.assert_called_once_with('IGVFFI6501YXMX')
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_from'].startswith('transcripts/')
    assert '_to' in first_item
    assert first_item['organism'] == 'Homo sapiens'
    assert first_item['source'] == 'Gene Ontology'
    assert first_item['source_url'] == GAF.SOURCES['rna']
    assert first_item['class'] == 'biological relationship'
    assert first_item['method'] is None
    assert first_item['label'] is None
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI6501YXMX'


def test_gaf_adapter_invalid_type():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_type. Allowed values: human, human_isoform, mouse, rna'):
        GAF(filepath='./samples/goa_human_sample.gaf.gz',
            label='invalid_type', writer=writer, validate=True)


def test_gaf_adapter_load_rnacentral_mapping():
    writer = SpyWriter()
    adapter = GAF(filepath='./samples/goa_human_rna.gaf.gz',
                  label='rna', writer=writer, validate=True)
    adapter.load_rnacentral_mapping()
    assert hasattr(adapter, 'rnacentral_mapping')
    assert isinstance(adapter.rnacentral_mapping, dict)
    assert len(adapter.rnacentral_mapping) > 0


def test_gaf_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = GAF(filepath='./samples/goa_human_sample.gaf.gz',
                  label='human', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_gaf_adapter_initialization():
    adapter = GAF(filepath='./samples/goa_human_sample.gaf.gz', label='human')
    assert adapter.filepath == './samples/goa_human_sample.gaf.gz'
    assert adapter.label == 'human'
    assert adapter.file_accession == 'goa_human_sample'
