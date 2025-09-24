import json
from unittest.mock import patch
import pytest

from adapters.pQTL_adapter import pQTL
from adapters.writer import SpyWriter


def test_pQTL_adapter(mocker):
    mocker.patch('adapters.pQTL_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    with patch('adapters.pQTL_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True
        adapter = pQTL(filepath='./samples/pQTL_UKB_example.csv',
                       label='pqtl', writer=writer, validate=True)
        adapter.process_file()
        assert len(writer.contents) == 768
        first_item = json.loads(writer.contents[0])
        assert first_item['_key'] == 'fake_variant_id_ENSP00000263100_UKB'
        assert first_item['name'] == 'associated with levels of'
        assert first_item['label'] == 'pQTL'
        assert first_item['log10pvalue'] == 79.2


def test_validate_doc_invalid(mocker):
    mocker.patch('adapters.pQTL_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    pqtl = pQTL(filepath='./samples/pQTL_UKB_example.csv',
                label='pqtl', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:.*doc:.*'):
        pqtl.validate_doc(invalid_doc)
