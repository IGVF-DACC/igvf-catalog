import json
import pytest
from unittest.mock import patch
from adapters.SEM_motif_adapter import SEMMotif
from adapters.writer import SpyWriter


FILE_ACCESSION = 'SEM_model_file'

# real uniprot -> ENSP mapping for P15923 (TCF3), used by the sample provenance file
SAMPLE_PROTEIN_MAP = {
    'P15923': ['ENSP00000262965', 'ENSP00000378813', 'ENSP00000468487']
}


@pytest.fixture
def mock_file_fileset():
    """Mock get_file_fileset_by_accession_in_arangodb so ArangoDB is not required."""
    with patch('adapters.SEM_motif_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'class': 'observed data',
            'method': 'SEMpl'
        }
        yield mock_get_file_fileset


@pytest.fixture
def mock_protein_map():
    """Mock get_protein_map_from_arangodb so ArangoDB is not required."""
    with patch('adapters.SEM_motif_adapter.get_protein_map_from_arangodb') as mock_get_protein_map:
        mock_get_protein_map.return_value = SAMPLE_PROTEIN_MAP
        yield mock_get_protein_map


def test_sem_motif_adapter_motif(mock_file_fileset, mock_protein_map):
    writer = SpyWriter()
    adapter = SEMMotif(filepath='./samples/SEM/SEM_model_file.tsv.gz',
                       sem_provenance_path='./samples/SEM/provenance_file.tsv.gz', label='motif', writer=writer, validate=True)
    adapter.process_file()
    mock_protein_map.assert_called_once_with(organism='Homo sapiens')
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert 'name' in first_item
    assert 'tf_name' in first_item
    assert 'source' in first_item
    assert 'source_url' in first_item
    assert 'pwm' in first_item
    assert 'length' in first_item
    assert first_item['class'] == 'observed data'
    assert first_item['method'] == 'SEMpl'
    assert first_item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


def test_sem_motif_adapter_motif_protein_link(mock_file_fileset, mock_protein_map):
    writer = SpyWriter()
    adapter = SEMMotif(filepath='./samples/SEM/SEM_model_file.tsv.gz', sem_provenance_path='./samples/SEM/provenance_file.tsv.gz',
                       label='motif_protein', writer=writer, validate=True)
    adapter.process_file()
    mock_protein_map.assert_called_once_with(organism='Homo sapiens')
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['_to'] == 'proteins/ENSP00000262965'
    assert 'name' in first_item
    assert 'inverse_name' in first_item
    assert 'biological_process' in first_item
    assert 'source' in first_item
    assert 'source_url' in first_item
    assert first_item['name'] == 'is used by'
    assert first_item['inverse_name'] == 'uses'
    assert first_item['biological_process'] == 'ontology_terms/GO_0003677'
    assert first_item['class'] == 'observed data'
    assert first_item['method'] == 'SEMpl'
    assert first_item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


def test_sem_motif_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: motif, motif_protein, complex, complex_protein'):
        SEMMotif(filepath='./samples/SEM/SEM_model_file.tsv.gz', sem_provenance_path='./samples/SEM/provenance_file.tsv.gz',
                 label='invalid_label', writer=writer)


def test_sem_motif_adapter_load_tf_id_mapping():
    adapter = SEMMotif(filepath='./samples/SEM/SEM_model_file.tsv.gz',
                       sem_provenance_path='./samples/SEM/provenance_file.tsv.gz')
    adapter.load_tf_id_mapping()
    assert hasattr(adapter, 'tf_id_mapping')
    assert isinstance(adapter.tf_id_mapping, dict)
    assert len(adapter.tf_id_mapping) > 0


def test_validate_doc_invalid():
    writer = SpyWriter()
    adapter = SEMMotif(filepath='./samples/SEM/SEM_model_file.tsv.gz',
                       sem_provenance_path='./samples/SEM/provenance_file.tsv.gz', label='motif', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
