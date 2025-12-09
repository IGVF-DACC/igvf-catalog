import json
import pytest
from adapters.SEM_prediction_adapter import SEMPred
from adapters.writer import SpyWriter
from unittest.mock import patch


# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test
@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.SEM_prediction_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'SEMVAR',
            'class': 'prediction',
            'samples': None,
            'simple_sample_summaries': None
        }
        yield mock_get_file_fileset


def test_sem_pred_adapter(mock_file_fileset):
    writer = SpyWriter()
    adapter = SEMPred(filepath='./samples/SEM/SEM_prediction_file.tsv.gz', sem_provenance_path='./samples/SEM/provenance_file.tsv.gz',
                      label='sem_predicted_asb', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'motif' in first_item
    assert 'ref_seq_context' in first_item
    assert 'alt_seq_context' in first_item
    assert 'ref_score' in first_item
    assert 'alt_score' in first_item
    assert 'variant_effect_score' in first_item
    assert 'SEMpl_annotation' in first_item
    assert 'SEMpl_baseline' in first_item
    assert 'files_filesets' in first_item
    assert 'biological_process' in first_item
    assert 'source' in first_item
    assert 'source_url' in first_item
    assert first_item['label'] == 'predicted allele-specific binding'
    assert first_item['biological_process'] == 'ontology_terms/GO_0051101'
    assert first_item['name'] == 'modulates binding of'
    assert first_item['inverse_name'] == 'binding modulated by'
    assert first_item['biosample_term'] is None
    assert first_item['biological_context'] is None
    assert first_item['method'] == 'SEMVAR'
    assert first_item['class'] == 'prediction'


def test_sem_pred_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: sem_predicted_asb'):
        SEMPred(filepath='./samples/SEM/SEM_prediction_file.tsv.gz', sem_provenance_path='./samples/SEM/provenance_file.tsv.gz',
                label='invalid_label', writer=writer)


def p():
    adapter = SEMPred(filepath='./samples/SEM/SEM_prediction_file.tsv.gz',
                      sem_provenance_path='./samples/SEM/provenance_file.tsv.gz')
    adapter.load_tf_id_mapping()
    assert hasattr(adapter, 'tf_id_mapping')
    assert isinstance(adapter.tf_id_mapping, dict)
    assert len(adapter.tf_id_mapping) > 0


def test_sem_pred_adapter_binding_effect_filtering(mock_file_fileset):
    writer = SpyWriter()
    adapter = SEMPred(filepath='./samples/SEM/SEM_prediction_file.tsv.gz', sem_provenance_path='./samples/SEM/provenance_file.tsv.gz',
                      label='sem_predicted_asb', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item['SEMpl_annotation'] in SEMPred.BINDING_EFFECT_LIST


def test_validate_doc_invalid():
    writer = SpyWriter()
    adapter = SEMPred(filepath='./samples/SEM/SEM_prediction_file.tsv.gz',
                      sem_provenance_path='./samples/SEM/provenance_file.tsv.gz', label='sem_predicted_asb', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
