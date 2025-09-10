import json
import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from adapters.gencode_adapter import Gencode
from adapters.writer import SpyWriter

try:
    from jsonschema.exceptions import ValidationError
except ImportError:
    # Fallback for different jsonschema versions
    from jsonschema import ValidationError


def test_gencode_adapter_transcript():
    writer = SpyWriter()
    adapter = Gencode(filepath='./samples/gencode_sample.gtf',
                      label='gencode_transcript', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert 'transcript_id' in first_item
    assert 'name' in first_item
    assert 'transcript_type' in first_item
    assert 'chr' in first_item
    assert 'start' in first_item
    assert 'end' in first_item
    assert 'gene_name' in first_item
    assert first_item['source'] == 'GENCODE'
    assert first_item['version'] == 'v43'
    assert first_item['source_url'] == 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz'


def test_gencode_adapter_transcribed_to():
    writer = SpyWriter()
    adapter = Gencode(filepath='./samples/gencode_sample.gtf',
                      label='transcribed_to', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['name'] == 'transcribes'
    assert first_item['inverse_name'] == 'transcribed by'
    assert first_item['biological_process'] == 'ontology_terms/GO_0010467'


def test_gencode_adapter_mouse():
    writer = SpyWriter()
    adapter = Gencode(filepath='./samples/gencode_mouse_sample.gtf',
                      label='mm_gencode_transcript', organism='MOUSE', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert first_item['source'] == 'GENCODE'
    assert first_item['source_url'] == 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M36/gencode.vM36.chr_patch_hapl_scaff.annotation.gtf.gz'
    assert first_item['version'] == 'vM36'


def test_gencode_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid labelS. Allowed values: gencode_transcript,mm_gencode_transcript,transcribed_to'):
        Gencode(filepath='./samples/gencode_sample.gtf',
                label='invalid_label', writer=writer)


def test_gencode_adapter_initialization():
    writer = SpyWriter()
    for label in Gencode.ALLOWED_LABELS:
        adapter = Gencode(filepath='./samples/gencode_sample.gtf',
                          label=label, writer=writer)
        assert adapter.filepath == './samples/gencode_sample.gtf'
        assert adapter.label == label
        assert adapter.dataset == label
        assert adapter.writer == writer

        if label in ['gencode_transcript', 'mm_gencode_transcript']:
            assert adapter.type == 'node'
        else:
            assert adapter.type == 'edge'


def test_gencode_adapter_parse_info_metadata():
    adapter = Gencode(filepath='./samples/gencode_sample.gtf',
                      label='gencode_transcript')
    info = ['gene_id', '"ENSG00000223972.5";', 'transcript_id', '"ENST00000456328.2";', 'gene_type', '"transcribed_unprocessed_pseudogene";',
            'gene_name', '"DDX11L1";', 'transcript_type', '"processed_transcript";', 'transcript_name', '"DDX11L1-202";']
    parsed_info = adapter.parse_info_metadata(info)
    assert parsed_info['gene_id'] == 'ENSG00000223972.5'
    assert parsed_info['transcript_id'] == 'ENST00000456328.2'
    assert parsed_info['gene_type'] == 'transcribed_unprocessed_pseudogene'
    assert parsed_info['gene_name'] == 'DDX11L1'
    assert parsed_info['transcript_type'] == 'processed_transcript'
    assert parsed_info['transcript_name'] == 'DDX11L1-202'


def test_gencode_adapter_validation_error():
    """Test that ValidationError is properly caught and converted to ValueError"""
    writer = SpyWriter()
    adapter = Gencode(filepath='./samples/gencode_sample.gtf',
                      label='gencode_transcript', writer=writer, validate=True)

    # Create an invalid document that will fail validation
    # Missing required fields like '_key', 'transcript_id', etc.
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }

    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_gencode_adapter_chr_name_mapping():
    """Test chromosome name mapping logic for lines 111-120"""
    writer = SpyWriter()

    # Create temporary GTF file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gtf', delete=False) as gtf_file:
        # Create GTF content with non-chr chromosome names
        gtf_content = """# Test GTF file
GL000008.2	HAVANA	gene	1	100	.	+	.	gene_id "ENSG00000101349.1"; gene_name "TEST_GENE"; gene_type "protein_coding";
GL000008.2	HAVANA	transcript	1	100	.	+	.	gene_id "ENSG00000101349.1"; transcript_id "ENST00000101349.1"; gene_name "TEST_GENE"; transcript_type "protein_coding"; transcript_name "TEST_GENE-001";
UNMAPPED_CHR	HAVANA	gene	1	100	.	+	.	gene_id "ENSG00000101350.1"; gene_name "TEST_GENE2"; gene_type "protein_coding";
NA_CHR	HAVANA	gene	1	100	.	+	.	gene_id "ENSG00000101351.1"; gene_name "TEST_GENE3"; gene_type "protein_coding";
"""
        gtf_file.write(gtf_content)
        gtf_file_path = gtf_file.name

    try:
        # Create adapter - it will automatically use the correct mapping file
        adapter = Gencode(filepath=gtf_file_path,
                          label='gencode_transcript', writer=writer, validate=False)

        # Process the file - this should trigger the chromosome mapping logic
        adapter.process_file()

        # Check that some records were processed (GL000008.2 should be mapped to chr4_GL000008v2_random)
        non_empty_contents = [
            content for content in writer.contents if content.strip()]
        assert len(non_empty_contents) > 0

        # Verify that GL000008.2 was mapped to chr4_GL000008v2_random
        processed_records = [json.loads(content)
                             for content in non_empty_contents]
        mapped_records = [record for record in processed_records if record.get(
            'chr') == 'chr4_GL000008v2_random']
        assert len(mapped_records) > 0

    finally:
        # Clean up temporary file
        os.unlink(gtf_file_path)
