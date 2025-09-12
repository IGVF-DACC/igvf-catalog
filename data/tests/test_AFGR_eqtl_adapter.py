import json
from unittest.mock import patch

from adapters.AFGR_eqtl_adapter import AFGREQtl
from adapters.writer import SpyWriter
import pytest


def test_AFGR_eqtl_adapter_AFGR_eqtl(mocker):
    writer = SpyWriter()
    mocker.patch('adapters.AFGR_eqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    with patch('adapters.AFGR_eqtl_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = AFGREQtl(
            filepath='./samples/AFGR/sorted.dist.hwe.af.AFR_META.eQTL.example.txt.gz',
            label='AFGR_eqtl',
            writer=writer,
            validate=True
        )
        adapter.process_file()

        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) == 200
        assert len(first_item) == 14
        assert first_item['inverse_name'] == 'expression modulated by'


def test_AFGR_eqtl_adapter_AFGR_eqtl_term(mocker):
    writer = SpyWriter()
    mocker.patch('adapters.AFGR_eqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    with patch('adapters.AFGR_eqtl_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True
        adapter = AFGREQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR_META.eQTL.example.txt.gz',
                           label='AFGR_eqtl_term', writer=writer, validate=True)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) == 200
        assert len(first_item) == 8
        assert first_item['inverse_name'] == 'has measurement'


def test_AFGR_eqtl_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError):
        adapter = AFGREQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR_META.eQTL.example.txt.gz',
                           label='invalid_label', writer=writer, validate=True)


def test_AFGR_eqtl_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = AFGREQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR_META.eQTL.example.txt.gz',
                       label='AFGR_eqtl_term', writer=writer, validate=True)

    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_AFGR_eqtl_adapter_AFGR_eqtl_invalid_gene_id(mocker):
    writer = SpyWriter()
    mocker.patch('adapters.AFGR_eqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')

    # Mock GeneValidator before creating the adapter
    with patch('adapters.AFGR_eqtl_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = False

        adapter = AFGREQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR_META.eQTL.example.txt.gz',
                           label='AFGR_eqtl', writer=writer, validate=True)
        adapter.process_file()
        assert len(writer.contents) == 0


def test_AFGR_eqtl_adapter_deletion_variant_skipped():
    """Test that deletion variants (alt='*') are skipped (covers line 64)"""
    writer = SpyWriter()

    # Create a temporary test file with a deletion variant
    import tempfile
    import gzip
    with tempfile.NamedTemporaryFile(suffix='.txt.gz', delete=False) as temp_file:
        with gzip.open(temp_file.name, 'wt') as f:
            f.write('chr\tsnp_pos\tsnp_pos2\tref\talt\teffect_af_eqtl\tvariant\tfeature\tlog10p\tpvalue\tbeta\tseqstat\tdf\tp_het\tp_hwe\tdist_start\tdist_end\tgeneSymbol\tgeneType\n')
            f.write('1\t12345\t12345\tA\t*\t1.0\t1_12345_A_*\tENSG00000123456.1\t6.0\t1e-06\t1.0\t0.3\tNA\t1.0\tNA\t1.0\t-100\t-200\tTEST_GENE\tprotein_coding\n')
        temp_file_path = temp_file.name

    try:
        adapter = AFGREQtl(filepath=temp_file_path,
                           label='AFGR_eqtl', writer=writer, validate=False)
        adapter.process_file()

        # Should have no output because deletion variant was skipped
        assert len(writer.contents) == 0

    finally:
        import os
        os.unlink(temp_file_path)
