import json
import pytest
from unittest.mock import patch
from adapters.proteins_interaction_adapter import ProteinsInteraction
from adapters.writer import SpyWriter


@pytest.fixture
def filepath():
    return './samples/IGVFFI4317VDGK.merged_PPI.UniProt.example.csv'


@pytest.fixture
def spy_writer():
    return SpyWriter()


@pytest.fixture
def mock_file_fileset():
    with patch('adapters.proteins_interaction_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get:
        mock_get.return_value = {
            'class': 'observed data',
            'method': 'affinity chromatography technology'
        }
        yield mock_get


@pytest.fixture
def mock_protein_map():
    with patch('adapters.protein_map.get_protein_map_from_arangodb') as mock_get:
        mock_get.return_value = {
            'Q9Y243': ['ENSP00000263816'],
            'Q9Y6H6': ['ENSP00000357431'],
            'P24844': ['ENSP00000261741'],
        }
        yield mock_get


def test_proteins_interaction_adapter(filepath, spy_writer, mock_file_fileset, mock_protein_map):
    adapter = ProteinsInteraction(
        filepath=filepath, label='protein_protein_human', writer=spy_writer, validate=True)
    adapter.process_file()

    mock_protein_map.assert_called_once_with(
        field='uniprot_ids',
        organism='Homo sapiens',
        dbxref_name=None,
    )
    assert len(spy_writer.contents) > 0
    first_item = json.loads(spy_writer.contents[0])

    assert '_key' in first_item
    assert first_item['_from'] == 'proteins/ENSP00000263816'
    assert first_item['_to'] == 'proteins/ENSP00000357431'
    assert 'detection_method' in first_item
    assert 'detection_method_code' in first_item
    assert 'interaction_type' in first_item
    assert 'interaction_type_code' in first_item
    assert 'confidence_value_biogrid' in first_item
    assert 'confidence_value_intact' in first_item
    assert 'source' in first_item
    assert 'pmids' in first_item
    assert 'organism' in first_item
    assert first_item['name'] == 'physically interacts with'
    assert first_item['inverse_name'] == 'physically interacts with'
    assert first_item['molecular_function'] == 'ontology_terms/GO_0005515'
    assert first_item['class'] == 'observed data'
    assert first_item['source_url'] == 'https://data.igvf.org/reference-files/IGVFFI4317VDGK'
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI4317VDGK'
    mock_file_fileset.assert_called_once_with('IGVFFI4317VDGK')


def test_proteins_interaction_adapter_initialization(filepath, spy_writer):
    adapter = ProteinsInteraction(
        filepath=filepath, label='protein_protein_human', writer=spy_writer)
    assert adapter.filepath == filepath
    assert adapter.label == 'protein_protein_human'
    assert adapter.organism == 'Homo sapiens'


def test_proteins_interaction_adapter_mouse(spy_writer):
    mouse_filepath = './samples/IGVFFI1165YVBA.merged_PPI_mouse.UniProt.example.csv'
    adapter = ProteinsInteraction(
        filepath=mouse_filepath, label='protein_protein_mouse', writer=spy_writer, validate=True)
    assert adapter.label == 'protein_protein_mouse'
    assert adapter.organism == 'Mus musculus'


def test_proteins_interaction_adapter_load_MI_code_mapping(filepath, spy_writer):
    adapter = ProteinsInteraction(
        filepath=filepath, label='protein_protein_human', writer=spy_writer)
    adapter.load_MI_code_mapping()
    assert hasattr(adapter, 'MI_code_mapping')
    assert isinstance(adapter.MI_code_mapping, dict)
    assert len(adapter.MI_code_mapping) > 0


def test_validate_doc_invalid(filepath, spy_writer):
    adapter = ProteinsInteraction(
        filepath=filepath, label='protein_protein_human', writer=spy_writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
