import json
from unittest.mock import patch

from adapters.AFGR_sqtl_adapter import AFGRSQtl
from adapters.writer import SpyWriter


def test_AFGR_sqtl_adapter_AFGR_sqtl(mocker):
    mocker.patch('adapters.AFGR_sqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    with patch('adapters.AFGR_sqtl_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True
        adapter = AFGRSQtl(filepath='./samples/AFGR/sorted.all.AFR.Meta.sQTL.example.txt.gz',
                           label='AFGR_sqtl', writer=writer)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) == 214
        assert len(first_item) == 17
        assert first_item['intron_chr'].startswith('chr')


def test_AFGR_sqtl_adapter_AFGR_sqtl_term(mocker):
    mocker.patch('adapters.AFGR_sqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    with patch('adapters.AFGR_sqtl_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True
        adapter = AFGRSQtl(filepath='./samples/AFGR/sorted.all.AFR.Meta.sQTL.example.txt.gz',
                           label='AFGR_sqtl_term', writer=writer)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) == 214
        assert len(first_item) == 8
        assert first_item['inverse_name'] == 'has measurement'
