import json
import pytest
from adapters.gencode_gene_structure_adapter import GencodeStructure
from adapters.writer import SpyWriter


def test_gencode_structure_adapter_gene_structure():
    writer = SpyWriter()
    adapter = GencodeStructure(
        filepath='./samples/gencode_sample.gtf', label='gene_structure', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert 'name' in first_item
    assert 'chr' in first_item
    assert 'start' in first_item
    assert 'end' in first_item
    assert 'strand' in first_item
    assert 'type' in first_item
    assert 'gene_id' in first_item
    assert 'gene_name' in first_item
    assert 'transcript_id' in first_item
    assert 'transcript_name' in first_item
    assert 'exon_number' in first_item
    assert 'exon_id' in first_item
    assert first_item['source'] == 'GENCODE'
    assert first_item['version'] == 'v43'
    assert first_item['source_url'] == 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz'
    assert first_item['organism'] == 'Homo sapiens'


def test_gencode_structure_adapter_mm_gene_structure():
    writer = SpyWriter()
    adapter = GencodeStructure(
        filepath='./samples/gencode_sample.gtf', label='mm_gene_structure', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert first_item['source'] == 'GENCODE'
    assert first_item['version'] == 'vM36'
    assert first_item['source_url'] == 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M36/gencode.vM36.chr_patch_hapl_scaff.annotation.gtf.gz'
    assert first_item['organism'] == 'Mus musculus'


def test_gencode_structure_adapter_transcript_contains_gene_structure():
    writer = SpyWriter()
    adapter = GencodeStructure(filepath='./samples/gencode_sample.gtf',
                               label='transcript_contains_gene_structure', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'name' in first_item
    assert 'inverse_name' in first_item
    assert first_item['source'] == 'GENCODE'
    assert first_item['version'] == 'v43'
    assert first_item['source_url'] == 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz'
    assert first_item['organism'] == 'Homo sapiens'


def test_gencode_structure_adapter_mm_transcript_contains_mm_gene_structure():
    writer = SpyWriter()
    adapter = GencodeStructure(filepath='./samples/gencode_sample.gtf',
                               label='mm_transcript_contains_mm_gene_structure', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['source'] == 'GENCODE'
    assert first_item['version'] == 'vM36'
    assert first_item['source_url'] == 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M36/gencode.vM36.chr_patch_hapl_scaff.annotation.gtf.gz'
    assert first_item['organism'] == 'Mus musculus'


def test_gencode_structure_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label. Allowed values: gene_structure,mm_gene_structure,transcript_contains_gene_structure,mm_transcript_contains_mm_gene_structure'):
        GencodeStructure(filepath='./samples/gencode_sample.gtf',
                         label='invalid_label', writer=writer)


def test_gencode_structure_adapter_initialization():
    writer = SpyWriter()
    for label in GencodeStructure.ALLOWED_LABELS:
        adapter = GencodeStructure(
            filepath='./samples/gencode_sample.gtf', label=label, writer=writer)
        assert adapter.filepath == './samples/gencode_sample.gtf'
        assert adapter.label == label
        assert adapter.writer == writer

        if label in ['gene_structure', 'mm_gene_structure']:
            assert adapter.type == 'node'
        else:
            assert adapter.type == 'edge'


def test_gencode_structure_adapter_parse_info_metadata():
    adapter = GencodeStructure(filepath='./samples/gencode_sample.gtf')
    info = ['gene_id', '"ENSG00000223972.5";', 'transcript_id', '"ENST00000456328.2";', 'gene_name',
            '"DDX11L1";', 'transcript_name', '"DDX11L1-202";', 'exon_number', '1', 'exon_id', '"ENSE00002234944.1";']
    parsed_info = adapter.parse_info_metadata(info)
    assert parsed_info['gene_id'] == 'ENSG00000223972.5'
    assert parsed_info['transcript_id'] == 'ENST00000456328.2'
    assert parsed_info['gene_name'] == 'DDX11L1'
    assert parsed_info['transcript_name'] == 'DDX11L1-202'
    assert parsed_info['exon_number'] == '1'
    assert parsed_info['exon_id'] == 'ENSE00002234944.1'
