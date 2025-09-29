import json
import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from adapters.mouse_genomes_project_adapter import MouseGenomesProjectAdapter
from adapters.writer import SpyWriter


@pytest.fixture
def sample_filepath():
    return './samples/mouse_variants/mouse_variant_snps_rsid_sample.vcf'


@pytest.fixture
def spy_writer():
    return SpyWriter()


@patch('adapters.helpers.get_seqrepo')
@patch('adapters.mouse_genomes_project_adapter.create_dataproxy')
@patch('adapters.mouse_genomes_project_adapter.SeqRepo')
@patch('adapters.mouse_genomes_project_adapter.Translator')
def test_mouse_genomes_project_adapter_process_file(mock_translator, mock_seqrepo, mock_dataproxy, mock_get_seqrepo, sample_filepath, spy_writer):
    """Test MouseGenomesProjectAdapter with mocked SeqRepo"""
    # Mock SeqRepo and related components
    mock_seqrepo_instance = MagicMock()
    mock_seqrepo.return_value = mock_seqrepo_instance

    mock_dataproxy_instance = MagicMock()
    mock_dataproxy.return_value = mock_dataproxy_instance

    mock_translator_instance = MagicMock()
    mock_translator.return_value = mock_translator_instance

    # Mock get_seqrepo
    mock_get_seqrepo.return_value = mock_seqrepo_instance

    # Mock build_spdi to return a predictable SPDI
    with patch('adapters.mouse_genomes_project_adapter.build_spdi') as mock_build_spdi:
        mock_build_spdi.return_value = 'NC_000001.11:3050050:C:G'

        adapter = MouseGenomesProjectAdapter(
            sample_filepath, writer=spy_writer, validate=True)
        adapter.process_file()

    assert len(spy_writer.contents) > 0
    # Check only the first item to make the test faster
    data = json.loads(spy_writer.contents[0])
    assert '_key' in data
    assert 'name' in data
    assert 'chr' in data
    assert 'pos' in data
    assert 'ref' in data
    assert 'alt' in data
    assert 'rsid' in data
    assert 'strain' in data
    assert 'qual' in data
    assert 'filter' in data
    assert 'fi' in data
    assert 'spdi' in data
    assert 'hgvs' in data
    assert 'organism' in data
    assert 'source' in data
    assert 'source_url' in data
    assert data['organism'] == 'Mus musculus'
    assert data['source'] == 'MOUSE GENOMES PROJECT'


@patch('adapters.helpers.get_seqrepo')
@patch('adapters.mouse_genomes_project_adapter.create_dataproxy')
@patch('adapters.mouse_genomes_project_adapter.SeqRepo')
@patch('adapters.mouse_genomes_project_adapter.Translator')
def test_mouse_genomes_project_adapter_initialization(mock_translator, mock_seqrepo, mock_dataproxy, mock_get_seqrepo, spy_writer):
    """Test adapter initialization"""
    adapter = MouseGenomesProjectAdapter(
        'test_file.vcf', writer=spy_writer, validate=True)

    assert adapter.filepath == 'test_file.vcf'
    assert adapter.label == 'mouse_variant'
    assert adapter.organism == 'Mus musculus'
    assert adapter.validate == True
    assert adapter.schema is not None
    assert adapter.validator is not None


@patch('adapters.helpers.get_seqrepo')
@patch('adapters.mouse_genomes_project_adapter.create_dataproxy')
@patch('adapters.mouse_genomes_project_adapter.SeqRepo')
@patch('adapters.mouse_genomes_project_adapter.Translator')
def test_mouse_genomes_project_adapter_validate_doc_invalid(mock_translator, mock_seqrepo, mock_dataproxy, mock_get_seqrepo, spy_writer):
    """Test document validation with invalid data"""
    adapter = MouseGenomesProjectAdapter(
        'test_file.vcf', writer=spy_writer, validate=True)

    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }

    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
