import json
import pytest
from adapters.SEM_motif_adapter import SEMMotif
from adapters.writer import SpyWriter


def test_sem_motif_adapter_motif():
    writer = SpyWriter()
    adapter = SEMMotif(filepath='./samples/SEM/', label='motif', writer=writer)
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
    assert first_item['source'] == SEMMotif.SOURCE
    assert first_item['source_url'] == SEMMotif.SOURCE_URL


def test_sem_motif_adapter_motif_protein_link():
    writer = SpyWriter()
    adapter = SEMMotif(filepath='./samples/SEM/',
                       label='motif_protein_link', writer=writer)
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
    assert first_item['source'] == SEMMotif.SOURCE
    assert first_item['source_url'] == SEMMotif.SOURCE_URL
    assert first_item['name'] == 'is used by'
    assert first_item['inverse_name'] == 'uses'
    assert first_item['biological_process'] == 'ontology_terms/GO_0003677'


def test_sem_motif_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label. Allowed values: motif,motif_protein_link'):
        SEMMotif(filepath='./samples/SEM/',
                 label='invalid_label', writer=writer)


def test_sem_motif_adapter_initialization():
    writer = SpyWriter()
    for label in SEMMotif.ALLOWED_LABELS:
        adapter = SEMMotif(filepath='./samples/SEM/',
                           label=label, writer=writer)
        assert adapter.filepath == './samples/SEM/'
        assert adapter.label == label
        assert adapter.dataset == label
        assert adapter.dry_run == True
        assert adapter.writer == writer
        if label == 'motif':
            assert adapter.type == 'node'
            assert adapter.collection == 'motifs'
        else:
            assert adapter.type == 'edge'
            assert adapter.collection == 'motifs_proteins'


def test_sem_motif_adapter_load_tf_id_mapping():
    adapter = SEMMotif(filepath='./samples/SEM/')
    adapter.load_tf_id_mapping()
    assert hasattr(adapter, 'tf_id_mapping')
    assert isinstance(adapter.tf_id_mapping, dict)
    assert len(adapter.tf_id_mapping) > 0
