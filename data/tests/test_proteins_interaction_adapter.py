import json
import pytest
from adapters.proteins_interaction_adapter import ProteinsInteraction
from adapters.writer import SpyWriter


@pytest.fixture
def filepath():
    return './samples/merged_PPI.UniProt.example.csv'


@pytest.fixture
def spy_writer():
    return SpyWriter()


def test_proteins_interaction_adapter(filepath, spy_writer):
    adapter = ProteinsInteraction(
        filepath=filepath, label='edge', writer=spy_writer)
    adapter.process_file()

    assert len(spy_writer.contents) > 0
    first_item = json.loads(spy_writer.contents[0])

    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'detection_method' in first_item
    assert 'detection_method_code' in first_item
    assert 'interaction_type' in first_item
    assert 'interaction_type_code' in first_item
    assert 'confidence_value_biogrid:long' in first_item
    assert 'confidence_value_intact:long' in first_item
    assert 'source' in first_item
    assert 'pmids' in first_item
    assert 'organism' in first_item
    assert first_item['name'] == 'physically interacts with'
    assert first_item['inverse_name'] == 'physically interacts with'
    assert first_item['molecular_function'] == 'ontology_terms/GO_0005515'


def test_proteins_interaction_adapter_initialization(filepath, spy_writer):
    adapter = ProteinsInteraction(
        filepath=filepath, label='edge', writer=spy_writer)
    assert adapter.filepath == filepath
    assert adapter.label == 'edge'
    assert adapter.dataset == 'edge'
    assert adapter.type == 'edge'
    assert adapter.organism == 'Homo sapiens'


def test_proteins_interaction_adapter_mouse(spy_writer):
    mouse_filepath = './samples/merged_PPI_mouse.UniProt.csv'
    adapter = ProteinsInteraction(
        filepath=mouse_filepath, label='edge', writer=spy_writer)
    assert adapter.organism == 'Mus musculus'


def test_proteins_interaction_adapter_load_MI_code_mapping(filepath, spy_writer):
    adapter = ProteinsInteraction(
        filepath=filepath, label='edge', writer=spy_writer)
    adapter.load_MI_code_mapping()
    assert hasattr(adapter, 'MI_code_mapping')
    assert isinstance(adapter.MI_code_mapping, dict)
    assert len(adapter.MI_code_mapping) > 0
