import json
import pytest
from adapters.SEM_motif_adapter import SEMMotif
from adapters.writer import SpyWriter


def test_sem_motif_adapter_motif():
    writer = SpyWriter()
    adapter = SEMMotif(filepath='./samples/SEM/SEM_model_file.tsv.gz',
                       sem_provenance_path='./samples/SEM/provenance_file.tsv.gz', label='motif', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert 'name' in first_item
    assert 'tf_name' in first_item
    assert 'source' in first_item
    assert 'source_url' in first_item
    assert 'pwm' in first_item
    assert 'length' in first_item


def test_sem_motif_adapter_motif_protein_link():
    writer = SpyWriter()
    adapter = SEMMotif(filepath='./samples/SEM/SEM_model_file.tsv.gz', sem_provenance_path='./samples/SEM/provenance_file.tsv.gz',
                       label='motif_protein', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'name' in first_item
    assert 'inverse_name' in first_item
    assert 'biological_process' in first_item
    assert 'source' in first_item
    assert 'source_url' in first_item
    assert first_item['name'] == 'is used by'
    assert first_item['inverse_name'] == 'uses'
    assert first_item['biological_process'] == 'ontology_terms/GO_0003677'


def test_sem_motif_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label. Allowed values: motif,motif_protein,complex,complex_protein'):
        SEMMotif(filepath='./samples/SEM/SEM_model_file.tsv.gz',
                 label='invalid_label', writer=writer)


def test_sem_motif_adapter_load_tf_id_mapping():
    adapter = SEMMotif(filepath='./samples/SEM/SEM_model_file.tsv.gz',
                       sem_provenance_path='./samples/SEM/provenance_file.tsv.gz')
    adapter.load_tf_id_mapping()
    assert hasattr(adapter, 'tf_id_mapping')
    assert isinstance(adapter.tf_id_mapping, dict)
    assert len(adapter.tf_id_mapping) > 0
