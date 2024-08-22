import json
import pytest
from adapters.gencode_gene_adapter import GencodeGene
from adapters.writer import SpyWriter


def test_gencode_gene_adapter_human():
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
    assert 'start:long' in first_item
    assert 'end:long' in first_item
    assert 'name' in first_item
    assert first_item['source'] == 'GENCODE'
    assert first_item['version'] == 'v43'
    assert first_item['source_url'] == 'https://www.gencodegenes.org/human/'


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


def test_gencode_gene_adapter_get_collection_alias():
    adapter = GencodeGene(filepath='./samples/gencode_sample.gtf',
                          gene_alias_file_path='./samples/Homo_sapiens.gene_info.gz')
    alias_dict = adapter.get_collection_alias()
    assert isinstance(alias_dict, dict)
    assert len(alias_dict) > 0
