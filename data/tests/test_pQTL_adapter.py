import json
from unittest.mock import patch
import pytest

from adapters.pQTL_adapter import pQTL
from adapters.writer import SpyWriter


def mock_igvf_metadata(mock_request):
    mock_request.return_value.json.return_value = {
        'catalog_class': 'observed data',
        'catalog_method': 'pQTL'
    }


@patch('adapters.pQTL_adapter.requests.get')
def test_pQTL_adapter(mock_request, mocker):
    mock_igvf_metadata(mock_request)
    mocker.patch('adapters.pQTL_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    with patch('adapters.pQTL_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True
        adapter = pQTL(filepath='./samples/pQTL_UKB_example.csv',
                       label='variant_protein', writer=writer, validate=True)
        adapter.file_accession = 'IGVFFI0000TEST'
        adapter.process_file()
        assert len(writer.contents) == 768
        first_item = json.loads(writer.contents[0])
        assert first_item['_key'] == 'fake_variant_id_ENSP00000263100_UKB'
        assert first_item['name'] == 'associated with levels of'
        assert first_item['label'] == 'pQTL'
        assert first_item['method'] == 'pQTL'
        assert first_item['class'] == 'observed data'
        assert first_item['log10pvalue'] == 79.2


def test_validate_doc_invalid(mocker):
    mocker.patch('adapters.pQTL_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    pqtl = pQTL(filepath='./samples/pQTL_UKB_example.csv',
                label='variant_protein', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        pqtl.validate_doc(invalid_doc)
