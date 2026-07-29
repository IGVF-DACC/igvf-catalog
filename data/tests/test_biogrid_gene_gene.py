import json
import pytest
from unittest.mock import patch

from adapters.biogrid_gene_gene_adapter import GeneGeneBiogrid
from adapters.writer import SpyWriter


@pytest.fixture
def mock_file_fileset():
    with patch('adapters.biogrid_gene_gene_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get:
        mock_get.return_value = {
            'class': 'observed data',
            'method': 'genetic interference'
        }
        yield mock_get


def test_biogrid_gene_gene_adapter_gene_gene_biogrid(mock_file_fileset):
    writer = SpyWriter()
    adapter = GeneGeneBiogrid(
        filepath='./samples/IGVFFI4317VDGK.merged_PPI.UniProt.example.csv', label='human_gene_gene_biogrid', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) == 2
    assert len(first_item) == 20
    assert first_item['source'] == 'BioGRID'
    assert first_item['confidence_value_biogrid'] is None
    assert first_item['class'] == 'observed data'
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI4317VDGK'
    assert first_item['interaction_type'] == [
        'positive genetic interaction (sensu BioGRID)']
    mock_file_fileset.assert_called_once_with('IGVFFI4317VDGK')


def test_biogrid_gene_gene_adapter_mouse_gene_gene_biogrid(mock_file_fileset):
    writer = SpyWriter()
    adapter = GeneGeneBiogrid(filepath='./samples/IGVFFI1165YVBA.merged_PPI_mouse.UniProt.example.csv',
                              label='mouse_gene_gene_biogrid', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) == 14
    assert len(first_item) == 20
    assert first_item['source'] == 'BioGRID'
    assert first_item['class'] == 'observed data'
    assert first_item['files_filesets'] == 'files_filesets/IGVFFI1165YVBA'
    assert first_item['interaction_type'] == [
        'positive genetic interaction (sensu BioGRID)']
    mock_file_fileset.assert_called_once_with('IGVFFI1165YVBA')


def test_biogrid_gene_gene_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = GeneGeneBiogrid(filepath='./samples/IGVFFI4317VDGK.merged_PPI.UniProt.example.csv',
                              label='human_gene_gene_biogrid', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
