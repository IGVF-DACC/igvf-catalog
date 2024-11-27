import json
import pytest
from adapters.gencode_adapter import Gencode
from adapters.writer import SpyWriter


def test_gencode_adapter_transcript():
    writer = SpyWriter()
    adapter = Gencode(filepath='./samples/gencode_sample.gtf',
                      label='gencode_transcript', writer=writer)
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
    assert first_item['source_url'] == 'https://www.gencodegenes.org/human/'


def test_gencode_adapter_transcribed_to():
    writer = SpyWriter()
    adapter = Gencode(filepath='./samples/gencode_sample.gtf',
                      label='transcribed_to', writer=writer)
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
    adapter = Gencode(filepath='./samples/gencode_sample.gtf',
                      label='mm_gencode_transcript', organism='MOUSE', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert first_item['source'] == 'GENCODE'
    assert first_item['version'] == 'vM33'
    assert first_item['source_url'] == 'https://www.gencodegenes.org/mouse/'


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
        assert adapter.dry_run == True
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
