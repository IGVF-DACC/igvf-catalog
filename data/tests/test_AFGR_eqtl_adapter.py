import json
from unittest.mock import patch

from adapters.AFGR_eqtl_adapter import AFGREQtl
from adapters.writer import SpyWriter


def test_AFGR_eqtl_adapter_AFGR_eqtl():
    writer = SpyWriter()
    with patch('adapters.AFGR_eqtl_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = AFGREQtl(
            filepath='./samples/AFGR/sorted.dist.hwe.af.AFR_META.eQTL.example.txt.gz',
            label='AFGR_eqtl',
            writer=writer
        )
        adapter.process_file()

        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) == 200
        assert len(first_item) == 14
        assert first_item['inverse_name'] == 'expression modulated by'


def test_AFGR_eqtl_adapter_AFGR_eqtl_term():
    writer = SpyWriter()
    with patch('adapters.AFGR_eqtl_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True
        adapter = AFGREQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR_META.eQTL.example.txt.gz',
                           label='AFGR_eqtl_term', writer=writer)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) == 200
        assert len(first_item) == 8
        assert first_item['inverse_name'] == 'has measurement'
