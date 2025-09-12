import json
from unittest.mock import patch
import pytest

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
                           label='AFGR_sqtl', writer=writer, validate=True)
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
                           label='AFGR_sqtl_term', writer=writer, validate=True)
        adapter.process_file()
        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) == 214
        assert len(first_item) == 8
        assert first_item['inverse_name'] == 'has measurement'


def test_AFGR_sqtl_adapter_AFGR_sqtl_term_invalid_label(mocker):
    writer = SpyWriter()
    with pytest.raises(ValueError):
        adapter = AFGRSQtl(filepath='./samples/AFGR/sorted.all.AFR.Meta.sQTL.example.txt.gz',
                           label='invalid_label', writer=writer, validate=True)


def test_AFGR_sqtl_adapter_AFGR_sqtl_term_validate_doc_invalid(mocker):
    mocker.patch('adapters.AFGR_sqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    with patch('adapters.AFGR_sqtl_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True
        adapter = AFGRSQtl(filepath='./samples/AFGR/sorted.all.AFR.Meta.sQTL.example.txt.gz',
                           label='AFGR_sqtl', writer=writer, validate=True)
        invalid_doc = {
            'invalid_field': 'invalid_value',
            'another_invalid_field': 123
        }
        with pytest.raises(ValueError, match='Document validation failed:'):
            adapter.validate_doc(invalid_doc)


def test_AFGR_sqtl_adapter_AFGR_sqtl_invalid_gene_id(mocker):
    mocker.patch('adapters.AFGR_sqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    with patch('adapters.AFGR_sqtl_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = False
        adapter = AFGRSQtl(filepath='./samples/AFGR/sorted.all.AFR.Meta.sQTL.example.txt.gz',
                           label='AFGR_sqtl', writer=writer, validate=True)
        adapter.process_file()
        assert len(writer.contents) == 0


def test_AFGR_sqtl_adapter_AFGR_sqtl_skip_alt_star():
    """Test that deletion variants (alt='*') are skipped (covers lines 70-71)"""
    writer = SpyWriter()

    # Create a temporary test file with a deletion variant
    import tempfile
    import gzip
    with tempfile.NamedTemporaryFile(suffix='.txt.gz', delete=False) as temp_file:
        with gzip.open(temp_file.name, 'wt') as f:
            f.write(
                'chr\tpos\tref\talt\tsnp\tfeature\tbeta\tse\tzstat\tp\t95pct_ci_lower\t95pct_ci_upper\tqstat\tdf\tp_het\n')
            f.write('chr1\t88338\tG\t*\t1_88338_G_*\t1:187577:187755:clu_2352\t0.0723108199416329\t0.0685894841949755\t1.05425519363987\t0.291766096608984\t-0.0621220987986983\t0.206743738681964\t1.23511015771854\t5\t0.941465002419174\n')
        temp_file_path = temp_file.name

    try:
        adapter = AFGRSQtl(filepath=temp_file_path,
                           label='AFGR_sqtl', writer=writer, validate=False)
        adapter.process_file()

        # Should have no output because deletion variant was skipped
        assert len(writer.contents) == 0

    finally:
        import os
        os.unlink(temp_file_path)


def test_AFGR_sqtl_adapter_no_gene_mapping():
    """Test that introns without gene mapping are skipped (covers lines 78-79)"""
    writer = SpyWriter()

    # Create a temporary test file with an intron that has no gene mapping
    import tempfile
    import gzip
    with tempfile.NamedTemporaryFile(suffix='.txt.gz', delete=False) as temp_file:
        with gzip.open(temp_file.name, 'wt') as f:
            f.write(
                'chr\tpos\tref\talt\tsnp\tfeature\tbeta\tse\tzstat\tp\t95pct_ci_lower\t95pct_ci_upper\tqstat\tdf\tp_het\n')
            f.write('chr1\t88338\tG\tA\t1_88338_G_A\tUNMAPPED_INTRON_ID\t0.0723108199416329\t0.0685894841949755\t1.05425519363987\t0.291766096608984\t-0.0621220987986983\t0.206743738681964\t1.23511015771854\t5\t0.941465002419174\n')
        temp_file_path = temp_file.name

    try:
        adapter = AFGRSQtl(filepath=temp_file_path,
                           label='AFGR_sqtl', writer=writer, validate=False)
        adapter.process_file()

        # Should have no output because intron has no gene mapping
        assert len(writer.contents) == 0

    finally:
        import os
        os.unlink(temp_file_path)
