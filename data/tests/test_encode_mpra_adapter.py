import json
import pytest
import tempfile
import gzip
import os
from unittest.mock import patch
from adapters.encode_mpra_adapter import EncodeMPRA
from adapters.writer import SpyWriter


# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test
@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.encode_mpra_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'MPRA',
            'class': 'observed data',
            'simple_sample_summaries': ['K562'],
            'samples': ['ontology_terms/EFO_0002067']
        }
        yield mock_get_file_fileset


def test_encode_mpra_adapter_regulatory_region(mock_file_fileset):
    writer = SpyWriter()

    # Create a small temporary test file
    with tempfile.NamedTemporaryFile(suffix='.bed.gz', delete=False) as temp_file:
        with gzip.open(temp_file.name, 'wt') as f:
            f.write(
                'chr1\t10410\t10610\tHepG2_DNasePeakNoPromoter1\t212\t+\t-0.843\t0.307\t0.171\t-1\t-1\n')
        temp_file_path = temp_file.name

    try:
        adapter = EncodeMPRA(filepath=temp_file_path,
                             label='genomic_element',
                             source_url='https://www.encodeproject.org/files/ENCFF802FUV/',
                             biological_context='EFO_0002067',
                             writer=writer,
                             validate=True)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) > 0
        assert '_key' in first_item
        assert 'chr' in first_item
        assert 'start' in first_item
        assert 'end' in first_item
        assert first_item['type'] == 'tested elements'
        assert first_item['source'] == EncodeMPRA.SOURCE
        assert first_item['source_url'] == 'https://www.encodeproject.org/files/ENCFF802FUV/'
    finally:
        os.unlink(temp_file_path)


def test_encode_mpra_adapter_regulatory_region_biosample(mock_file_fileset):
    writer = SpyWriter()

    # Create a small temporary test file
    with tempfile.NamedTemporaryFile(suffix='.bed.gz', delete=False) as temp_file:
        with gzip.open(temp_file.name, 'wt') as f:
            f.write(
                'chr1\t10410\t10610\tHepG2_DNasePeakNoPromoter1\t212\t+\t-0.843\t0.307\t0.171\t-1\t-1\n')
        temp_file_path = temp_file.name

    try:
        adapter = EncodeMPRA(filepath=temp_file_path,
                             label='genomic_element_biosample',
                             source_url='https://www.encodeproject.org/files/ENCFF802FUV/',
                             biological_context='EFO_0002067',
                             writer=writer,
                             validate=True)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) > 0
        assert '_key' in first_item
        assert '_from' in first_item
        assert '_to' in first_item
        assert 'element_name' in first_item
        assert 'strand' in first_item
        assert 'activity_score' in first_item
        assert 'bed_score' in first_item
        assert 'DNA_count' in first_item
        assert 'RNA_count' in first_item
        assert first_item['method'] == 'MPRA'
        assert first_item['class'] == 'observed data'
        assert first_item['label'] == 'regulatory element activity'
        assert first_item['source'] == EncodeMPRA.SOURCE
        assert first_item['source_url'] == 'https://www.encodeproject.org/files/ENCFF802FUV/'
    finally:
        os.unlink(temp_file_path)


def test_encode_mpra_adapter_invalid_label(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: genomic_element, genomic_element_biosample'):
        EncodeMPRA(filepath='dummy.bed.gz',
                   label='invalid_label',
                   source_url='https://www.encodeproject.org/files/ENCFF802FUV/',
                   biological_context='EFO_0002067',
                   writer=writer)


def test_encode_mpra_adapter_initialization(mock_file_fileset):
    writer = SpyWriter()
    for label in EncodeMPRA.ALLOWED_LABELS:
        adapter = EncodeMPRA(filepath='dummy.bed.gz',
                             label=label,
                             source_url='https://www.encodeproject.org/files/ENCFF802FUV/',
                             biological_context='EFO_0002067',
                             writer=writer)
        assert adapter.filepath == 'dummy.bed.gz'
        assert adapter.label == label
        assert adapter.source_url == 'https://www.encodeproject.org/files/ENCFF802FUV/'
        assert adapter.file_accession == 'ENCFF802FUV'
        assert adapter.biological_context == 'EFO_0002067'
        assert adapter.writer == writer


def test_encode_mpra_adapter_validate_doc_invalid(mock_file_fileset):
    writer = SpyWriter()
    adapter = EncodeMPRA(filepath='dummy.bed.gz',
                         label='genomic_element',
                         source_url='https://www.encodeproject.org/files/ENCFF802FUV/',
                         biological_context='EFO_0002067',
                         writer=writer,
                         validate=True)

    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }

    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
