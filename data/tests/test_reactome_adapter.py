import json
import pytest
from unittest.mock import patch
from adapters.reactome_adapter import Reactome
from adapters.writer import SpyWriter


@pytest.fixture
def filepath():
    return './samples/reactome/Ensembl2Reactome_All_Levels_sample.txt'


@pytest.fixture
def parent_pathway_of_filepath():
    return './samples/reactome/ReactomePathwaysRelation_20240603.txt'


@pytest.fixture
def spy_writer():
    return SpyWriter()


def test_reactome_adapter_genes_pathways(filepath, spy_writer):
    with patch('adapters.reactome_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True
        adapter = Reactome(filepath=filepath,
                           label='genes_pathways', writer=spy_writer, validate=True)
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


def test_reactome_adapter_parent_pathway_of(parent_pathway_of_filepath, spy_writer):
    adapter = Reactome(filepath=parent_pathway_of_filepath,
                       label='parent_pathway_of', writer=spy_writer, validate=True)
    adapter.process_file()
    assert len(spy_writer.contents) > 0
    first_item = json.loads(spy_writer.contents[0])
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['name'] == 'parent of'
    assert first_item['inverse_name'] == 'child of'
    assert first_item['source'] == 'Reactome'
    assert first_item['source_url'] == 'https://reactome.org/'


def test_reactome_adapter_initialization(filepath, spy_writer):
    with patch('adapters.reactome_adapter.GeneValidator'):
        adapter = Reactome(filepath=filepath,
                           label='genes_pathways', writer=spy_writer)
        assert adapter.filepath == filepath
        assert adapter.label == 'genes_pathways'


def test_reactome_adapter_invalid_label(filepath, spy_writer):
    with pytest.raises(ValueError):
        Reactome(filepath=filepath, label='invalid_label', writer=spy_writer)


def test_reactome_adapter_validate_doc_invalid(parent_pathway_of_filepath, spy_writer):
    adapter = Reactome(filepath=parent_pathway_of_filepath,
                       label='parent_pathway_of', writer=spy_writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_reactome_adapter_genes_pathways_invalid_gene_id(filepath, spy_writer):
    with patch('adapters.reactome_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = False
        adapter = Reactome(filepath=filepath,
                           label='genes_pathways', writer=spy_writer, validate=True)
        adapter.process_file()
        assert len(spy_writer.contents) == 0
