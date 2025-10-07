import json
import pytest
from unittest.mock import patch
from adapters.orphanet_disease_adapter import Disease
from adapters.writer import SpyWriter


@pytest.fixture
def sample_filepath():
    return './samples/orphanet_example.xml'


@pytest.fixture
def spy_writer():
    return SpyWriter()


def test_process_file(sample_filepath, spy_writer):
    with patch('adapters.orphanet_disease_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True
        disease = Disease(sample_filepath, writer=spy_writer, validate=True)
        disease.process_file()

        assert len(spy_writer.contents) > 0
        data = json.loads(spy_writer.contents[0])
        assert '_key' in data
        assert '_from' in data
        assert '_to' in data
        assert 'name' in data
        assert 'inverse_name' in data
        assert 'pmid' in data
        assert 'term_name' in data
        assert 'gene_symbol' in data
        assert 'association_type' in data
        assert 'association_status' in data
        assert 'source' in data
        assert 'source_url' in data
        assert data['name'] == 'associated_with'
        assert data['inverse_name'] == 'associated_with'
        assert data['source'] == Disease.SOURCE
        assert data['source_url'] == Disease.SOURCE_URL


def test_validate_doc_invalid(sample_filepath, spy_writer):
    with patch('adapters.orphanet_disease_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True
        disease = Disease(sample_filepath, writer=spy_writer, validate=True)
        invalid_doc = {
            'invalid_field': 'invalid_value',
            'another_invalid_field': 123
        }
        with pytest.raises(ValueError, match='Document validation failed:'):
            disease.validate_doc(invalid_doc)
