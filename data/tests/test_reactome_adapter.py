import json
import pytest
from adapters.reactome_adapter import Reactome
from adapters.writer import SpyWriter


@pytest.fixture
def filepath():
    return './samples/reactome/Ensembl2Reactome_All_Levels_sample.txt'


@pytest.fixture
def spy_writer():
    return SpyWriter()


def test_reactome_adapter_genes_pathways(filepath, spy_writer):
    adapter = Reactome(filepath=filepath,
                       label='genes_pathways', writer=spy_writer)
    adapter.process_file()

    assert len(spy_writer.contents) > 0
    first_item = json.loads(spy_writer.contents[0])

    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['name'] == 'belongs to'
    assert first_item['inverse_name'] == 'has part'
    assert first_item['source'] == 'Reactome'
    assert first_item['source_url'] == 'https://reactome.org/'


def test_reactome_adapter_initialization(filepath, spy_writer):
    adapter = Reactome(filepath=filepath,
                       label='genes_pathways', writer=spy_writer)
    assert adapter.filepath == filepath
    assert adapter.label == 'genes_pathways'
    assert adapter.dataset == 'genes_pathways'
    assert adapter.type == 'edge'


def test_reactome_adapter_invalid_label(filepath, spy_writer):
    with pytest.raises(ValueError):
        Reactome(filepath=filepath, label='invalid_label', writer=spy_writer)
