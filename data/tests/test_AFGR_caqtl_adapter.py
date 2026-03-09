import json

from adapters.AFGR_caqtl_adapter import AFGRCAQtl
from adapters.writer import SpyWriter
import pytest
from unittest.mock import patch


def mock_igvf_metadata(mock_request):
    mock_request.return_value.json.return_value = {
        'catalog_class': 'observed data',
        'catalog_method': 'caQTL'
    }


@patch('adapters.AFGR_caqtl_adapter.requests.get')
def test_AFGR_caqtl_adapter_regulatory_region(mock_request):
    mock_igvf_metadata(mock_request)
    writer = SpyWriter()
    adapter = AFGRCAQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR.caQTL.example.txt.gz',
                        label='genomic_element', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) == 200
    assert len(first_item) == 9
    assert first_item['_key'] == 'accessible_dna_element_1_906596_907043_GRCh38_AFGR'
    assert first_item['method'] == 'caQTL'


@patch('adapters.AFGR_caqtl_adapter.requests.get')
def test_AFGR_caqtl_adapter_AFGR_caqtl(mock_request, mocker):
    mock_igvf_metadata(mock_request)
    mocker.patch('adapters.AFGR_caqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    adapter = AFGRCAQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR.caQTL.example.txt.gz',
                        label='AFGR_caqtl', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) == 200
    assert len(first_item) == 15
    assert '_from' in first_item
    assert first_item['_key'] == 'fake_variant_id_accessible_dna_element_1_906596_907043_GRCh38_AFGR'
    assert first_item['method'] == 'caQTL'
    assert first_item['class'] == 'observed data'


def test_AFGR_caqtl_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError):
        adapter = AFGRCAQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR.caQTL.example.txt.gz',
                            label='invalid_label', writer=writer, validate=True)


def test_AFGR_caqtl_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = AFGRCAQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR.caQTL.example.txt.gz',
                        label='AFGR_caqtl', writer=writer, validate=True)

    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
