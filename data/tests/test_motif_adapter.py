import json
import pytest
from adapters.motif_adapter import Motif
from adapters.writer import SpyWriter


@pytest.fixture
def sample_filepath():
    return './samples/motifs'


@pytest.fixture
def spy_writer():
    return SpyWriter()


def test_motif_node(sample_filepath, spy_writer):
    motif = Motif(sample_filepath, label='motif',
                  writer=spy_writer, validate=True)
    motif.process_file()

    assert len(spy_writer.contents) > 0
    data = json.loads(spy_writer.contents[0])
    assert '_key' in data
    assert 'name' in data
    assert 'tf_name' in data
    assert 'source' in data
    assert 'source_url' in data
    assert 'pwm' in data
    assert 'length' in data
    assert data['source'] == Motif.SOURCE
    assert data['source_url'].startswith(Motif.SOURCE_URL)


def test_motif_protein_link(sample_filepath, spy_writer):
    motif = Motif(sample_filepath, label='motif_protein_link',
                  writer=spy_writer)
    motif.process_file()

    assert len(spy_writer.contents) > 0
    data = json.loads(spy_writer.contents[0])
    assert '_key' in data
    assert '_from' in data
    assert '_to' in data
    assert 'name' in data
    assert 'inverse_name' in data
    assert 'biological_process' in data
    assert 'source' in data
    assert data['name'] == 'is used by'
    assert data['inverse_name'] == 'uses'
    assert data['biological_process'] == 'ontology_terms/GO_0003677'
    assert data['source'] == Motif.SOURCE


def test_invalid_label(sample_filepath, spy_writer):
    with pytest.raises(ValueError):
        Motif(sample_filepath, label='invalid_label', writer=spy_writer)


def test_load_tf_uniprot_id_mapping(sample_filepath, spy_writer):
    motif = Motif(sample_filepath, label='motif_protein_link',
                  writer=spy_writer)
    motif.load_tf_ensembl_id_mapping()

    assert hasattr(motif, 'tf_ensembl_id_mapping')
    assert len(motif.tf_ensembl_id_mapping) > 0
