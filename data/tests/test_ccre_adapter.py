import json
import pytest
from unittest.mock import patch
from adapters.ccre_adapter import CCRE
from adapters.writer import SpyWriter


@pytest.mark.external_dependency
@patch('adapters.ccre_adapter.FileFileSet')
def test_ccre_adapter(mock_file_fileset):
    # Mock the FileFileSet to avoid external API calls
    mock_instance = mock_file_fileset.return_value
    mock_instance.query_fileset_files_props_encode.return_value = [
        {'method': 'candidate Cis-Regulatory Elements'}]

    writer = SpyWriter()
    adapter = CCRE(filepath='./samples/ENCFF420VPZ.example.bed.gz',
                   label='genomic_element', writer=writer)
    adapter.process_file()
    assert len(writer.contents) == 5510
    first_item = json.loads(writer.contents[0])
    assert first_item['_key'] == 'candidate_cis_regulatory_element_chr20_9550320_9550587_GRCh38_ENCFF420VPZ'
    assert first_item['chr'] == 'chr20'
    assert first_item['source_url'].startswith(
        'https://www.encodeproject.org/files/')


def test_ccre_adapter_initialization():
    adapter = CCRE(filepath='./samples/ENCFF167FJQ.example.bed.gz',
                   label='custom_label')
    assert adapter.filepath == './samples/ENCFF167FJQ.example.bed.gz'
    assert adapter.label == 'custom_label'
    assert adapter.dataset == 'custom_label'
    assert adapter.source_url.startswith(
        'https://www.encodeproject.org/files/')
    assert adapter.type == 'node'
