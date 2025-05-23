import json
import pytest
from adapters.encode_caqtl_adapter import CAQtl
from adapters.writer import SpyWriter


def test_caqtl_adapter_regulatory_region():
    writer = SpyWriter()
    adapter = CAQtl(filepath='./samples/caqtl-sample.bed',
                    source='PMID:34017130', label='genomic_element', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert 'chr' in first_item
    assert 'start' in first_item
    assert 'end' in first_item
    assert first_item['type'] == 'accessible dna elements'


def test_caqtl_adapter_encode_caqtl(mocker):
    mocker.patch('adapters.encode_caqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    adapter = CAQtl(filepath='./samples/caqtl-sample.bed',
                    source='PMID:34017130', label='encode_caqtl', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['label'] == 'caQTL'
    assert first_item['name'] == 'modulates accessibility of'
    assert first_item['inverse_name'] == 'accessibility modulated by'


def test_caqtl_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label. Allowed values: genomic_element,encode_caqtl'):
        CAQtl(filepath='./samples/caqtl-sample.bed',
              source='PMID:34017130', label='invalid_label', writer=writer)


def test_caqtl_adapter_initialization():
    writer = SpyWriter()
    for label in CAQtl.ALLOWED_LABELS:
        adapter = CAQtl(filepath='./samples/caqtl-sample.bed',
                        source='PMID:34017130', label=label, writer=writer)
        assert adapter.filepath == './samples/caqtl-sample.bed'
        assert adapter.label == label
        assert adapter.dataset == label
        assert adapter.source == 'PMID:34017130'
        assert adapter.dry_run == True
        assert adapter.writer == writer

        if label == 'genomic_element':
            assert adapter.type == 'node'
        else:
            assert adapter.type == 'edge'
