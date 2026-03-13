import json
import gzip
import os
import pytest
import tempfile
from unittest.mock import patch
from adapters.gencode_gene_adapter import GencodeGene
from adapters.writer import SpyWriter


@pytest.fixture(autouse=True)
def setup_before_each_test():
    # Create a temporary gene info file for testing instead of modifying the original
    with tempfile.NamedTemporaryFile(suffix='.gz', delete=False) as temp_file:
        with gzip.open(temp_file.name, 'wt') as f:
            f.write('test line\n')
        # Store the temp file path for tests to use
        import os
        os.environ['TEST_GENE_INFO_PATH'] = temp_file.name


@patch('requests.get')
def test_gencode_gene_adapter_human(mock_get):
    mock_response = {'@graph': []}
    mock_get.return_value.json.return_value = mock_response

    writer = SpyWriter()
    adapter = GencodeGene(filepath='./samples/gencode_sample.gtf',
                          gene_alias_file_path=os.environ.get(
                              'TEST_GENE_INFO_PATH', './samples/Homo_sapiens.gene_info.gz'),
                          label='gencode_gene',
                          writer=writer,
                          validate=True)
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
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: gencode_gene, mm_gencode_gene'):
        GencodeGene(filepath='./samples/gencode_sample.gtf',
                    gene_alias_file_path=os.environ.get(
                        'TEST_GENE_INFO_PATH', './samples/Homo_sapiens.gene_info.gz'),
                    label='invalid_label',
                    writer=writer)


def test_gencode_gene_adapter_parse_info_metadata():
    adapter = GencodeGene(filepath='./samples/gencode_sample.gtf',
                          gene_alias_file_path=os.environ.get('TEST_GENE_INFO_PATH', './samples/Homo_sapiens.gene_info.gz'))
    info = ['gene_id', '"ENSG00000223972.5";', 'gene_type',
            '"transcribed_unprocessed_pseudogene";', 'gene_name', '"DDX11L1";']
    parsed_info = adapter.parse_info_metadata(info)
    assert parsed_info['gene_id'] == 'ENSG00000223972.5'
    assert parsed_info['gene_type'] == 'transcribed_unprocessed_pseudogene'
    assert parsed_info['gene_name'] == 'DDX11L1'


def test_gencode_gene_adapter_mouse():
    writer = SpyWriter()
    adapter = GencodeGene(filepath='./samples/gencode_mouse_sample.gtf',
                          gene_alias_file_path='./samples/Mus_musculus.gene_info.gz',
                          label='mm_gencode_gene',
                          writer=writer,
                          validate=True)
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
    assert first_item['version'] == 'vM36'
    assert first_item['source_url'] == 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M36/gencode.vM36.chr_patch_hapl_scaff.annotation.gtf.gz'
    assert first_item['organism'] == 'Mus musculus'


def test_gencode_gene_adapter_not_catalog():
    writer = SpyWriter()
    adapter = GencodeGene(filepath='./samples/gencode_sample.gtf',
                          gene_alias_file_path=os.environ.get(
                              'TEST_GENE_INFO_PATH', './samples/Homo_sapiens.gene_info.gz'),
                          label='gencode_gene',
                          writer=writer,
                          validate=True,
                          mode='igvfd')
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert 'geneid' in first_item
    assert 'locations' in first_item
    assert 'symbol' in first_item
    assert 'taxa' in first_item
    assert 'transcriptome_annotation' in first_item
    assert 'version_number' in first_item


def test_gencode_gene_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = GencodeGene(filepath='./samples/gencode_sample.gtf',
                          gene_alias_file_path=os.environ.get(
                              'TEST_GENE_INFO_PATH', './samples/Homo_sapiens.gene_info.gz'),
                          label='gencode_gene',
                          writer=writer,
                          validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_gencode_gene_adapter_invalid_mode():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid mode. Allowed values: igvfd,catalog'):
        GencodeGene(filepath='./samples/gencode_sample.gtf',
                    gene_alias_file_path=os.environ.get(
                        'TEST_GENE_INFO_PATH', './samples/Homo_sapiens.gene_info.gz'),
                    label='gencode_gene',
                    writer=writer,
                    mode='invalid_mode')


def test_gencode_gene_adapter_chr_name_mapping():
    """Test chromosome name mapping logic - simplified test that focuses on the mapping logic"""
    writer = SpyWriter()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.gtf', delete=False) as gtf_file:
        gtf_file.write('''# Test GTF file
GL000008.2	HAVANA	gene	1	100	.	+	.	gene_id "ENSG00000101349.1"; gene_name "TEST_GENE"; gene_type "protein_coding";
''')
        gtf_file_path = gtf_file.name

    try:
        adapter = GencodeGene(filepath=gtf_file_path,
                              gene_alias_file_path=os.environ.get(
                                  'TEST_GENE_INFO_PATH', './samples/Homo_sapiens.gene_info.gz'),
                              label='gencode_gene', mode='igvfd', writer=writer, validate=False)
        adapter.process_file()

        # Check that some records were processed
        non_empty_contents = [
            content for content in writer.contents if content.strip()]
        assert len(non_empty_contents) > 0

        # Verify that GL000008.2 was mapped to chr4_GL000008v2_random
        processed_records = [json.loads(content)
                             for content in non_empty_contents]
        mapped_records = [record for record in processed_records if 'locations' in record and
                          any(loc.get('chromosome') == 'chr4_GL000008v2_random' for loc in record['locations'])]
        assert len(mapped_records) > 0

        first_item = mapped_records[0]
        assert first_item['symbol'] == 'TEST_GENE'
        assert first_item['taxa'] == 'Homo sapiens'

    finally:
        # Clean up temporary files
        os.unlink(gtf_file_path)
