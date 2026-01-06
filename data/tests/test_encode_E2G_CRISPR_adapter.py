import json
import pytest
from unittest.mock import patch
from adapters.encode_E2G_CRISPR_adapter import ENCODE2GCRISPR
from adapters.writer import SpyWriter


# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test
@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.encode_E2G_CRISPR_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'CRISPR enhancer perturbation screens',
            'class': 'observed data',
            'simple_sample_summaries': ['K562'],
            'samples': ['ontology_terms/EFO_0002067']
        }
        yield mock_get_file_fileset


@pytest.mark.external_dependency
def test_encode2gcrispr_adapter_regulatory_region(mock_file_fileset):
    writer = SpyWriter()
    adapter = ENCODE2GCRISPR(
        filepath='./samples/ENCODE_E2G_CRISPR_example.tsv', label='genomic_element', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert 'chr' in first_item
    assert 'start' in first_item
    assert 'end' in first_item
    assert 'type' in first_item
    assert first_item['method'] == 'CRISPR enhancer perturbation screens'
    assert first_item['source'] == ENCODE2GCRISPR.SOURCE
    assert first_item['source_url'] == ENCODE2GCRISPR.SOURCE_URL


@pytest.mark.external_dependency
def test_encode2gcrispr_adapter_regulatory_region_gene(mock_file_fileset):
    writer = SpyWriter()
    adapter = ENCODE2GCRISPR(filepath='./samples/ENCODE_E2G_CRISPR_example.tsv',
                             label='genomic_element_gene', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'score' in first_item
    assert 'p_value' in first_item
    assert 'log10pvalue' in first_item
    assert 'significant' in first_item
    assert first_item['source'] == ENCODE2GCRISPR.SOURCE
    assert first_item['source_url'] == ENCODE2GCRISPR.SOURCE_URL
    assert first_item['biological_context'] == 'K562'
    assert first_item['biosample_term'] == 'ontology_terms/EFO_0002067'
    assert first_item['label'] == 'regulatory element effect on gene expression'
    assert first_item['method'] == 'CRISPR enhancer perturbation screens'
    assert first_item['class'] == 'observed data'


def test_encode2gcrispr_adapter_invalid_label(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: genomic_element, genomic_element_gene'):
        ENCODE2GCRISPR(filepath='./samples/ENCODE_E2G_CRISPR_example.tsv',
                       label='invalid_label', writer=writer)


def test_encode2gcrispr_adapter_initialization(mock_file_fileset):
    writer = SpyWriter()
    for label in ENCODE2GCRISPR.ALLOWED_LABELS:
        adapter = ENCODE2GCRISPR(
            filepath='./samples/ENCODE_E2G_CRISPR_example.tsv', label=label, writer=writer)
        assert adapter.filepath == './samples/ENCODE_E2G_CRISPR_example.tsv'
        assert adapter.label == label
        assert adapter.writer == writer
        assert adapter.files_filesets is not None


def test_encode2gcrispr_adapter_load_regulatory_region(mock_file_fileset):
    writer = SpyWriter()
    adapter = ENCODE2GCRISPR(
        filepath='./samples/ENCODE_E2G_CRISPR_example.tsv', label='genomic_element', writer=writer)
    adapter.load_genomic_element()
    assert hasattr(adapter, 'genomic_element_nodes')
    assert isinstance(adapter.genomic_element_nodes, dict)
    assert len(adapter.genomic_element_nodes) > 0


def test_encode2gcrispr_adapter_load_gene_id_mapping(mock_file_fileset):
    writer = SpyWriter()
    adapter = ENCODE2GCRISPR(filepath='./samples/ENCODE_E2G_CRISPR_example.tsv',
                             label='genomic_element_gene', writer=writer)
    adapter.load_gene_id_mapping()
    assert hasattr(adapter, 'gene_id_mapping')
    assert isinstance(adapter.gene_id_mapping, dict)
    assert len(adapter.gene_id_mapping) > 0


def test_encode2gcrispr_adapter_validate_doc_invalid(mock_file_fileset):
    writer = SpyWriter()
    adapter = ENCODE2GCRISPR(filepath='./samples/ENCODE_E2G_CRISPR_example.tsv',
                             label='genomic_element_gene', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
