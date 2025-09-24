import json
import pytest
import tempfile
import gzip
import os
from unittest.mock import patch, MagicMock
from adapters.eqtl_catalog_adapter import EQTLCatalog
from adapters.writer import SpyWriter


@patch('adapters.helpers.get_seqrepo')
@patch('adapters.eqtl_catalog_adapter.GeneValidator')
def test_eqtl_catalog_adapter_qtl(mock_gene_validator, mock_get_seqrepo):
    # Mock GeneValidator
    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = True
    mock_gene_validator.return_value = mock_validator_instance

    # Mock SeqRepo
    mock_seqrepo = MagicMock()
    mock_get_seqrepo.return_value = mock_seqrepo

    writer = SpyWriter()

    # Create a small temporary test file with correct dataset ID
    with tempfile.NamedTemporaryFile(prefix='QTD000001.', suffix='.credible_sets.tsv.gz', delete=False) as temp_file:
        with gzip.open(temp_file.name, 'wt') as f:
            f.write(
                'molecular_trait_id\tgene_id\tcs_id\tvariant\trsid\tcs_size\tpip\tpvalue\tbeta\tse\tz\tcs_min_r2\tregion\n')
            f.write('ENSG00000230489\tENSG00000230489\tENSG00000230489_L1\tchr1_108004887_G_T\trs1936009\t53\t0.0197781278649429\t7.46541e-09\t0.767387\t0.116543\t7.19210214446939\t0.945192225726688\tchr1:106964443-108964443\n')
        temp_file_path = temp_file.name

    try:
        adapter = EQTLCatalog(filepath=temp_file_path,
                              label='qtl',
                              writer=writer,
                              validate=True)
        adapter.process_file()

        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) > 0
        assert '_key' in first_item
        assert '_from' in first_item
        assert '_to' in first_item
        assert 'molecular_trait_id' in first_item
        assert 'credible_set_id' in first_item
        assert 'variant_chromosome_position_ref_alt' in first_item
        assert 'rsid' in first_item
        assert 'credible_set_size' in first_item
        assert 'posterior_inclusion_probability' in first_item
        assert 'p_value' in first_item
        assert 'beta' in first_item
        assert 'standard_error' in first_item
        assert 'z_score' in first_item
        assert 'credible_set_min_r2' in first_item
        assert 'region' in first_item
        assert 'log10pvalue' in first_item
        assert 'source' in first_item
        assert first_item['source'] == 'eQTL Catalogue'
    finally:
        os.unlink(temp_file_path)


@patch('adapters.helpers.get_seqrepo')
@patch('adapters.eqtl_catalog_adapter.GeneValidator')
def test_eqtl_catalog_adapter_skips_invalid_gene_id(mock_gene_validator, mock_get_seqrepo):
    # Mock GeneValidator to return False for invalid gene ID
    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = False
    mock_gene_validator.return_value = mock_validator_instance

    # Mock SeqRepo
    mock_seqrepo = MagicMock()
    mock_get_seqrepo.return_value = mock_seqrepo

    writer = SpyWriter()

    # Create a small temporary test file with invalid gene ID
    with tempfile.NamedTemporaryFile(prefix='QTD000001.', suffix='.credible_sets.tsv.gz', delete=False) as temp_file:
        with gzip.open(temp_file.name, 'wt') as f:
            f.write(
                'molecular_trait_id\tgene_id\tcs_id\tvariant\trsid\tcs_size\tpip\tpvalue\tbeta\tse\tz\tcs_min_r2\tregion\n')
            f.write('INVALID_GENE\tINVALID_GENE\tINVALID_GENE_L1\tchr1_108004887_G_T\trs1936009\t53\t0.0197781278649429\t7.46541e-09\t0.767387\t0.116543\t7.19210214446939\t0.945192225726688\tchr1:106964443-108964443\n')
        temp_file_path = temp_file.name

    try:
        adapter = EQTLCatalog(filepath=temp_file_path,
                              label='qtl',
                              writer=writer,
                              validate=True)
        adapter.process_file()

        # Should skip the row with invalid gene ID
        assert len(writer.contents) == 0
    finally:
        os.unlink(temp_file_path)


def test_eqtl_catalog_adapter_initialization():
    writer = SpyWriter()
    for label in EQTLCatalog.ALLOWED_LABELS:
        adapter = EQTLCatalog(filepath='dummy.tsv.gz',
                              label=label,
                              writer=writer)
        assert adapter.filepath == 'dummy.tsv.gz'
        assert adapter.label == label
        assert adapter.type == 'edge'
        assert adapter.writer == writer
        assert adapter.source == 'eQTL Catalogue'


def test_eqtl_catalog_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label. Allowed values: qtl,study'):
        EQTLCatalog(filepath='dummy.tsv.gz',
                    label='invalid_label',
                    writer=writer)


def test_eqtl_catalog_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = EQTLCatalog(filepath='dummy.tsv.gz',
                          label='qtl',
                          writer=writer,
                          validate=True)

    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }

    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


def test_eqtl_catalog_adapter_study_label():
    """Test adapter with 'study' label"""
    writer = SpyWriter()

    # Create a temporary metadata file for study processing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as temp_metadata:
        temp_metadata.write(
            'study_id\tdataset_id\tstudy_label\tsample_group\ttissue_id\ttissue_label\tcondition_label\tsample_size\tquant_method\tpmid\tstudy_type\n')
        temp_metadata.write(
            'QTS000001\tQTD000001\tAlasoo_2018\tmacrophage_naive\tCL_0000235\tmacrophage\tnaive\t84\tge\t29379200\tbulk\n')
        temp_metadata_path = temp_metadata.name

    # Create a temporary study file with correct format (matching metadata columns)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as temp_study:
        temp_study.write(
            'study_id\tdataset_id\tstudy_label\tsample_group\ttissue_id\ttissue_label\tcondition_label\tsample_size\tquant_method\tpmid\tstudy_type\n')
        temp_study.write(
            'QTS000001\tQTD000001\tAlasoo_2018\tmacrophage_naive\tCL_0000235\tmacrophage\tnaive\t84\tge\t29379200\tbulk\n')
        temp_study_path = temp_study.name

    try:
        # Mock the METADATA_PATH to use our temporary file
        with patch.object(EQTLCatalog, 'METADATA_PATH', temp_metadata_path):
            adapter = EQTLCatalog(filepath=temp_study_path,
                                  label='study',
                                  writer=writer,
                                  validate=True)
            adapter.process_file()

        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) > 0
        assert '_key' in first_item
        assert 'name' in first_item
        assert 'pmid' in first_item
        assert 'study_type' in first_item
        assert 'source' in first_item
        assert first_item['source'] == 'eQTL Catalogue'
    finally:
        os.unlink(temp_metadata_path)
        os.unlink(temp_study_path)


@patch('adapters.helpers.get_seqrepo')
@patch('adapters.eqtl_catalog_adapter.GeneValidator')
def test_eqtl_catalog_adapter_pvalue_zero(mock_gene_validator, mock_get_seqrepo):
    """Test handling of p_value = 0"""
    # Mock GeneValidator
    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = True
    mock_gene_validator.return_value = mock_validator_instance

    # Mock SeqRepo
    mock_seqrepo = MagicMock()
    mock_get_seqrepo.return_value = mock_seqrepo

    writer = SpyWriter()

    # Create a test file with p_value = 0
    with tempfile.NamedTemporaryFile(prefix='QTD000001.', suffix='.credible_sets.tsv.gz', delete=False) as temp_file:
        with gzip.open(temp_file.name, 'wt') as f:
            f.write(
                'molecular_trait_id\tgene_id\tcs_id\tvariant\trsid\tcs_size\tpip\tpvalue\tbeta\tse\tz\tcs_min_r2\tregion\n')
            f.write('ENSG00000230489\tENSG00000230489\tENSG00000230489_L1\tchr1_108004887_G_T\trs1936009\t53\t0.0197781278649429\t0\t0.767387\t0.116543\t7.19210214446939\t0.945192225726688\tchr1:106964443-108964443\n')
        temp_file_path = temp_file.name

    try:
        adapter = EQTLCatalog(filepath=temp_file_path,
                              label='qtl',
                              writer=writer,
                              validate=True)
        adapter.process_file()

        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) > 0
        assert first_item['log10pvalue'] == EQTLCatalog.MAX_LOG10_PVALUE
    finally:
        os.unlink(temp_file_path)


@patch('adapters.helpers.get_seqrepo')
@patch('adapters.eqtl_catalog_adapter.GeneValidator')
def test_eqtl_catalog_adapter_splice_qtl_intron_fields(mock_gene_validator, mock_get_seqrepo):
    """Test splice QTL with intron fields"""
    # Mock GeneValidator
    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = True
    mock_gene_validator.return_value = mock_validator_instance

    # Mock SeqRepo
    mock_seqrepo = MagicMock()
    mock_get_seqrepo.return_value = mock_seqrepo

    writer = SpyWriter()

    # Create a temporary metadata file with exon quant_method for splice QTL
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as temp_metadata:
        temp_metadata.write(
            'study_id\tdataset_id\tstudy_label\tsample_group\ttissue_id\ttissue_label\tcondition_label\tsample_size\tquant_method\tftp_path\tftp_cs_path\tftp_lbf_path\n')
        temp_metadata.write(
            'QTS000001\tQTD000001\tAlasoo_2018\tmacrophage_naive\tCL_0000235\tmacrophage\tnaive\t84\texon\thttp://example.com\thttp://example.com\thttp://example.com\n')
        temp_metadata_path = temp_metadata.name

    # Create a test file with splice QTL format
    with tempfile.NamedTemporaryFile(prefix='QTD000001.', suffix='.credible_sets.tsv.gz', delete=False) as temp_file:
        with gzip.open(temp_file.name, 'wt') as f:
            f.write(
                'molecular_trait_id\tgene_id\tcs_id\tvariant\trsid\tcs_size\tpip\tpvalue\tbeta\tse\tz\tcs_min_r2\tregion\n')
            f.write('1:111139666:111140038:clu_35622_+\tENSG00000156171\t1:111139666:111140038:clu_35622_+_L1\tchr1_111108395_A_G\trs1583746\t4\t0.0680237702993137\t6.38809e-23\t-1.26169\t0.0859151\t-15.6241987461368\t0.948125027936558\tchr1:110138815-112138815\n')
        temp_file_path = temp_file.name

    try:
        # Mock the METADATA_PATH to use our temporary file
        with patch.object(EQTLCatalog, 'METADATA_PATH', temp_metadata_path):
            adapter = EQTLCatalog(filepath=temp_file_path,
                                  label='qtl',
                                  writer=writer,
                                  validate=True)
            adapter.process_file()

        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) > 0
        assert 'intron_chr' in first_item
        assert 'intron_start' in first_item
        assert 'intron_end' in first_item
        assert first_item['intron_chr'] == '1'
        assert first_item['intron_start'] == '111139666'
        assert first_item['intron_end'] == '111140038'
    finally:
        os.unlink(temp_file_path)
        os.unlink(temp_metadata_path)


def test_eqtl_catalog_adapter_no_metadata_found():
    """Test error when no metadata is found for dataset"""
    writer = SpyWriter()

    # Create a test file with unknown dataset ID
    with tempfile.NamedTemporaryFile(prefix='UNKNOWN.', suffix='.credible_sets.tsv.gz', delete=False) as temp_file:
        with gzip.open(temp_file.name, 'wt') as f:
            f.write(
                'molecular_trait_id\tgene_id\tcs_id\tvariant\trsid\tcs_size\tpip\tpvalue\tbeta\tse\tz\tcs_min_r2\tregion\n')
            f.write('ENSG00000230489\tENSG00000230489\tENSG00000230489_L1\tchr1_108004887_G_T\trs1936009\t53\t0.0197781278649429\t7.46541e-09\t0.767387\t0.116543\t7.19210214446939\t0.945192225726688\tchr1:106964443-108964443\n')
        temp_file_path = temp_file.name

    try:
        adapter = EQTLCatalog(filepath=temp_file_path,
                              label='qtl',
                              writer=writer,
                              validate=True)

        with pytest.raises(ValueError, match='No metadata found for dataset UNKNOWN'):
            adapter.process_file()
    finally:
        os.unlink(temp_file_path)
