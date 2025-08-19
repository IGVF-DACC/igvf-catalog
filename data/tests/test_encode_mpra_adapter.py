import json
import pytest
from adapters.encode_mpra_adapter import EncodeMPRA
from adapters.writer import SpyWriter


@pytest.mark.external_dependency
def test_encode_mpra_adapter_regulatory_region():
    writer = SpyWriter()
    adapter = EncodeMPRA(filepath='./samples/MPRA_ENCFF802FUV_example.bed.gz',
                         label='genomic_element',
                         source_url='https://www.encodeproject.org/files/ENCFF802FUV/',
                         biological_context='EFO_0002067',
                         writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert 'chr' in first_item
    assert 'start' in first_item
    assert 'end' in first_item
    assert first_item['type'] == 'tested elements'
    assert first_item['source'] == EncodeMPRA.SOURCE
    assert first_item['source_url'] == 'https://www.encodeproject.org/files/ENCFF802FUV/'


@pytest.mark.external_dependency
def test_encode_mpra_adapter_regulatory_region_biosample():
    writer = SpyWriter()
    adapter = EncodeMPRA(filepath='./samples/MPRA_ENCFF802FUV_example.bed.gz',
                         label='genomic_element_biosample',
                         source_url='https://www.encodeproject.org/files/ENCFF802FUV/',
                         biological_context='EFO_0002067',
                         writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'element_name' in first_item
    assert 'strand' in first_item
    assert 'activity_score' in first_item
    assert 'bed_score' in first_item
    assert 'DNA_count' in first_item
    assert 'RNA_count' in first_item
    assert first_item['source'] == EncodeMPRA.SOURCE
    assert first_item['source_url'] == 'https://www.encodeproject.org/files/ENCFF802FUV/'


def test_encode_mpra_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Ivalid label. Allowed values: genomic_element,genomic_element_biosample'):
        EncodeMPRA(filepath='./samples/MPRA_ENCFF802FUV_example.bed.gz',
                   label='invalid_label',
                   source_url='https://www.encodeproject.org/files/ENCFF802FUV/',
                   biological_context='EFO_0002067',
                   writer=writer)


def test_encode_mpra_adapter_initialization():
    writer = SpyWriter()
    for label in EncodeMPRA.ALLOWED_LABELS:
        adapter = EncodeMPRA(filepath='./samples/MPRA_ENCFF802FUV_example.bed.gz',
                             label=label,
                             source_url='https://www.encodeproject.org/files/ENCFF802FUV/',
                             biological_context='EFO_0002067',
                             writer=writer)
        assert adapter.filepath == './samples/MPRA_ENCFF802FUV_example.bed.gz'
        assert adapter.label == label
        assert adapter.dataset == label
        assert adapter.source_url == 'https://www.encodeproject.org/files/ENCFF802FUV/'
        assert adapter.file_accession == 'ENCFF802FUV'
        assert adapter.biological_context == 'EFO_0002067'
        assert adapter.writer == writer

        if label == 'genomic_element':
            assert adapter.type == 'node'
        else:
            assert adapter.type == 'edge'
