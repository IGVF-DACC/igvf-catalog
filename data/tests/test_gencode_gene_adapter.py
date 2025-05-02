import json
import gzip
import pytest
from unittest.mock import patch
from adapters.gencode_gene_adapter import GencodeGene
from adapters.writer import SpyWriter


@pytest.fixture(autouse=True)
def setup_before_each_test():
    with gzip.open('./samples/Homo_sapiens.gene_info.gz', 'wb') as f:
        text = 'test line\n'
        f.write(text.encode('utf-8'))


@patch('requests.get')
def test_gencode_gene_adapter_human(mock_get):
    mock_response = {'@graph': []}
    mock_get.return_value.json.return_value = mock_response

    writer = SpyWriter()
    adapter = GencodeGene(filepath='./samples/gencode_sample.gtf',
                          gene_alias_file_path='./samples/Homo_sapiens.gene_info.gz',
                          label='gencode_gene',
                          writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert 'gene_id' in first_item
    assert 'gene_type' in first_item
    assert 'chr' in first_item
    assert 'start' in first_item
    assert 'end' in first_item
    assert 'name' in first_item
    assert first_item['source'] == 'GENCODE'
    assert first_item['version'] == 'v43'
    assert first_item['source_url'] == 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz'


def test_gencode_gene_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label. Allowed values: gencode_gene,mm_gencode_gene'):
        GencodeGene(filepath='./samples/gencode_sample.gtf',
                    gene_alias_file_path='./samples/Homo_sapiens.gene_info.gz',
                    label='invalid_label',
                    writer=writer)


def test_gencode_gene_adapter_parse_info_metadata():
    adapter = GencodeGene(filepath='./samples/gencode_sample.gtf',
                          gene_alias_file_path='./samples/Homo_sapiens.gene_info.gz')
    info = ['gene_id', '"ENSG00000223972.5";', 'gene_type',
            '"transcribed_unprocessed_pseudogene";', 'gene_name', '"DDX11L1";']
    parsed_info = adapter.parse_info_metadata(info)
    assert parsed_info['gene_id'] == 'ENSG00000223972.5'
    assert parsed_info['gene_type'] == 'transcribed_unprocessed_pseudogene'
    assert parsed_info['gene_name'] == 'DDX11L1'
