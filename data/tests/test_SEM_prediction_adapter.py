import json
import pytest
from adapters.SEM_prediction_adapter import SEMPred
from adapters.writer import SpyWriter


def test_sem_pred_adapter():
    writer = SpyWriter()
    adapter = SEMPred(filepath='./samples/SEM/',
                      label='sem_predicted_asb', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'label' in first_item
    assert 'motif' in first_item
    assert 'kmer_chr' in first_item
    assert 'kmer_start' in first_item
    assert 'kmer_end' in first_item
    assert 'ref_score' in first_item
    assert 'alt_score' in first_item
    assert 'relative_binding_affinity' in first_item
    assert 'effect_on_binding' in first_item
    assert 'name' in first_item
    assert 'inverse_name' in first_item
    assert 'biological_process' in first_item
    assert 'source' in first_item
    assert 'source_url' in first_item
    assert first_item['label'] == 'predicted allele specific binding'
    assert first_item['source'] == SEMPred.SOURCE
    assert first_item['source_url'] == SEMPred.SOURCE_URL
    assert first_item['biological_process'] == 'ontology_terms/GO_0051101'
    assert first_item['name'] == 'modulates binding of'
    assert first_item['inverse_name'] == 'binding modulated by'


def test_sem_pred_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label. Allowed values: sem_predicted_asb'):
        SEMPred(filepath='./samples/SEM/',
                label='invalid_label', writer=writer)


def test_sem_pred_adapter_initialization():
    writer = SpyWriter()
    adapter = SEMPred(filepath='./samples/SEM/',
                      label='sem_predicted_asb', writer=writer)
    assert adapter.filepath == './samples/SEM/'
    assert adapter.label == 'sem_predicted_asb'
    assert adapter.dataset == 'sem_predicted_asb'
    assert adapter.type == 'edge'
    assert adapter.dry_run == True
    assert adapter.writer == writer


def test_sem_pred_adapter_load_tf_id_mapping():
    adapter = SEMPred(filepath='./samples/SEM/')
    adapter.load_tf_id_mapping()
    assert hasattr(adapter, 'tf_id_mapping')
    assert isinstance(adapter.tf_id_mapping, dict)
    assert len(adapter.tf_id_mapping) > 0


def test_sem_pred_adapter_binding_effect_filtering():
    writer = SpyWriter()
    adapter = SEMPred(filepath='./samples/SEM/',
                      label='sem_predicted_asb', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item['effect_on_binding'] in SEMPred.BINDING_EFFECT_LIST
