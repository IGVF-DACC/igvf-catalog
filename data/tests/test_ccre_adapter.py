import json
import pytest
from adapters.ccre_adapter import CCRE
from adapters.writer import SpyWriter
from unittest.mock import patch

# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test


@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.ccre_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'candidate Cis-Regulatory Elements',
            'class': 'observed data'
        }
        yield mock_get_file_fileset


@pytest.mark.external_dependency
def test_ccre_adapter(mock_file_fileset):
    writer = SpyWriter()
    adapter = CCRE(filepath='./samples/ENCFF420VPZ.example.bed.gz',
                   label='genomic_element', writer=writer, validate=True)
    adapter.process_file()
    assert len(writer.contents) == 5510
    first_item = json.loads(writer.contents[0])
    assert first_item['_key'] == 'candidate_cis_regulatory_element_chr20_9550320_9550587_GRCh38_ENCFF420VPZ'
    assert first_item['chr'] == 'chr20'
    assert first_item['source_url'].startswith(
        'https://www.encodeproject.org/files/')


def test_ccre_adapter_initialization():
    adapter = CCRE(filepath='./samples/ENCFF167FJQ.example.bed.gz',
                   label='genomic_element')
    assert adapter.label == 'genomic_element'
    assert adapter.filename == 'ENCFF167FJQ'
    assert adapter.source_url.startswith(
        'https://www.encodeproject.org/files/')
    assert adapter._get_collection_name() == 'genomic_elements'


def test_ccre_adapter_mm_genomic_element_collection_name():
    """Test that mm_genomic_element label returns correct collection name."""
    adapter = CCRE(filepath='./samples/ENCFF167FJQ.example.bed.gz',
                   label='mm_genomic_element')
    assert adapter.label == 'mm_genomic_element'
    assert adapter._get_collection_name() == 'mm_genomic_elements'


def test_ccre_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = CCRE(filepath='./samples/ENCFF420VPZ.example.bed.gz',
                   label='genomic_element', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
