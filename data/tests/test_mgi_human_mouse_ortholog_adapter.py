import json
import pytest
from adapters.mgi_human_mouse_ortholog_adapter import MGIHumanMouseOrthologAdapter
from adapters.writer import SpyWriter


@pytest.fixture
def sample_filepath():
    return './samples/HOM_MouseHumanSequence_sample.rpt'


@pytest.fixture
def spy_writer():
    return SpyWriter()


def test_process_file(sample_filepath, spy_writer):
    adapter = MGIHumanMouseOrthologAdapter(sample_filepath, writer=spy_writer)
    adapter.process_file()

    assert len(spy_writer.contents) > 0
    # Check only the first item to make the test faster
    data = json.loads(spy_writer.contents[0])
    assert '_key' in data
    assert '_from' in data
    assert '_to' in data
    assert data['_from'].startswith('genes/')
    assert data['_to'].startswith('mm_genes/')
    assert data['name'] == 'homologous to'
    assert data['inverse_name'] == 'homologous to'
    assert data['relationship'] == 'ontology_terms/NCIT_C79968'
    assert data['source'] == 'MGI'
    assert data['source_url'] == 'https://www.informatics.jax.org/downloads/reports/HOM_MouseHumanSequence.rpt'


def test_load_mappings(sample_filepath, spy_writer):
    adapter = MGIHumanMouseOrthologAdapter(sample_filepath, writer=spy_writer)
    adapter.load_mgi_ensembl_mapping()
    adapter.load_entrz_ensembl_mapping()

    assert hasattr(adapter, 'mm_gene_mapping')
    assert len(adapter.mm_gene_mapping) > 0
    assert hasattr(adapter, 'gene_mapping')
    assert len(adapter.gene_mapping) > 0
