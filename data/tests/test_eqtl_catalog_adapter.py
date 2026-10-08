import json
import pytest
import tempfile
import gzip
import os
from unittest.mock import patch, MagicMock
from adapters.eqtl_catalog_adapter import EQTLCatalog
from adapters.writer import SpyWriter


def mock_portal_aliases(mock_request, dataset_id='QTD000001'):
    mock_request.return_value.json.return_value = {
        'aliases': [f'igvf:igvf_catalog_ebi_eqtl_{dataset_id}']
    }


@pytest.fixture
def mock_file_fileset_eqtl():
    with patch('adapters.eqtl_catalog_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get:
        mock_get.return_value = {
            'class': 'observed data',
            'method': 'eQTL'
        }
        yield mock_get


@pytest.fixture
def mock_file_fileset_splice_qtl():
    with patch('adapters.eqtl_catalog_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get:
        mock_get.return_value = {
            'class': 'observed data',
            'method': 'spliceQTL'
        }
        yield mock_get


@pytest.fixture
def mock_bulk_check_variants():
    """Mock bulk_check_variants_in_arangodb. Defaults to treating every
    computed variant id as already loaded, so tests that aren't specifically
    exercising the existence check still see edges emitted; override
    .side_effect/.return_value in a test to exercise the skip path."""
    with patch('adapters.eqtl_catalog_adapter.bulk_check_variants_in_arangodb') as mock_check:
        mock_check.side_effect = lambda variant_ids, **kwargs: set(
            variant_ids)
        yield mock_check


@patch('adapters.eqtl_catalog_adapter.requests.get')
@patch('adapters.helpers.get_seqrepo')
@patch('adapters.eqtl_catalog_adapter.GeneValidator')
def test_eqtl_catalog_adapter_qtl(mock_gene_validator, mock_get_seqrepo, mock_request, mock_file_fileset_eqtl, mock_bulk_check_variants):
    mock_portal_aliases(mock_request)
    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = True
    mock_gene_validator.return_value = mock_validator_instance

    mock_seqrepo = MagicMock()
    mock_get_seqrepo.return_value = mock_seqrepo

    writer = SpyWriter()

    with tempfile.NamedTemporaryFile(prefix='IGVFFI0000TEST.', suffix='.tsv.gz', delete=False) as temp_file:
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

        mock_file_fileset_eqtl.assert_called_once_with('IGVFFI0000TEST')
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
        assert 'effect_size' in first_item
        assert 'standard_error' in first_item
        assert 'z_score' in first_item
        assert 'credible_set_min_r2' in first_item
        assert 'region' in first_item
        assert 'neg_log10_pvalue' in first_item
        assert first_item['source'] == adapter.source
        assert first_item['class'] == 'observed data'
        assert first_item['method'] == 'eQTL'
        assert first_item['label'] == 'eQTL'
        assert first_item['files_filesets'] == 'files_filesets/IGVFFI0000TEST'
    finally:
        os.unlink(temp_file_path)


@patch('adapters.eqtl_catalog_adapter.requests.get')
@patch('adapters.helpers.get_seqrepo')
@patch('adapters.eqtl_catalog_adapter.GeneValidator')
def test_eqtl_catalog_adapter_skips_invalid_gene_id(mock_gene_validator, mock_get_seqrepo, mock_request, mock_file_fileset_eqtl, mock_bulk_check_variants):
    mock_portal_aliases(mock_request)
    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = False
    mock_gene_validator.return_value = mock_validator_instance

    mock_seqrepo = MagicMock()
    mock_get_seqrepo.return_value = mock_seqrepo

    writer = SpyWriter()

    with tempfile.NamedTemporaryFile(prefix='IGVFFI0000TEST.', suffix='.tsv.gz', delete=False) as temp_file:
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
        assert adapter.writer == writer
        assert adapter.source == 'EBI'
        assert adapter.gene_validator is not None


def test_eqtl_catalog_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: qtl, study, variants'):
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

    with tempfile.NamedTemporaryFile(mode='wb', suffix='.tsv.gz', delete=False) as temp_study:
        with gzip.open(temp_study, 'wt') as gz:
            gz.write(
                'study_id\tdataset_id\tstudy_label\tsample_group\ttissue_id\ttissue_label\tcondition_label\tsample_size\tquant_method\tpmid\tstudy_type\n')
            gz.write(
                'QTS000001\tQTD000001\tAlasoo_2018\tmacrophage_naive\tCL_0000235\tmacrophage\tnaive\t84\tge\t29379200\tbulk\n')
        temp_study_path = temp_study.name

    try:
        adapter = EQTLCatalog(filepath=temp_study_path,
                              label='study',
                              writer=writer,
                              validate=True)
        adapter.process_file()

        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) > 0
        assert '_key' in first_item
        assert first_item['_key'] == 'QTS000001'
        assert 'name' in first_item
        assert first_item['name'] == 'Alasoo_2018'
        assert 'pmid' in first_item
        assert first_item['pmid'] == '29379200'
        assert 'study_type' in first_item
        assert first_item['study_type'] == 'bulk'
        assert 'source' in first_item
        assert first_item['source'] == 'EBI'
        assert 'source_url' in first_item
        assert first_item['source_url'] == EQTLCatalog.STUDY_SOURCE_URL
        assert first_item['files_filesets'] == 'files_filesets/' + \
            os.path.basename(temp_study_path).split('.')[0]
    finally:
        os.unlink(temp_study_path)


@patch('adapters.eqtl_catalog_adapter.requests.get')
@patch('adapters.helpers.get_seqrepo')
@patch('adapters.eqtl_catalog_adapter.GeneValidator')
def test_eqtl_catalog_adapter_pvalue_zero(mock_gene_validator, mock_get_seqrepo, mock_request, mock_file_fileset_eqtl, mock_bulk_check_variants):
    mock_portal_aliases(mock_request)
    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = True
    mock_gene_validator.return_value = mock_validator_instance

    mock_seqrepo = MagicMock()
    mock_get_seqrepo.return_value = mock_seqrepo

    writer = SpyWriter()

    with tempfile.NamedTemporaryFile(prefix='IGVFFI0000TEST.', suffix='.tsv.gz', delete=False) as temp_file:
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
        assert first_item['neg_log10_pvalue'] == EQTLCatalog.MAX_LOG10_PVALUE
    finally:
        os.unlink(temp_file_path)


@patch('adapters.eqtl_catalog_adapter.requests.get')
@patch('adapters.helpers.get_seqrepo')
@patch('adapters.eqtl_catalog_adapter.GeneValidator')
def test_eqtl_catalog_adapter_splice_qtl_intron_fields(mock_gene_validator, mock_get_seqrepo, mock_request, mock_file_fileset_splice_qtl, mock_bulk_check_variants):
    mock_portal_aliases(mock_request)
    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = True
    mock_gene_validator.return_value = mock_validator_instance

    mock_seqrepo = MagicMock()
    mock_get_seqrepo.return_value = mock_seqrepo

    writer = SpyWriter()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as temp_metadata:
        temp_metadata.write(
            'study_id\tdataset_id\tstudy_label\tsample_group\ttissue_id\ttissue_label\tcondition_label\tsample_size\tquant_method\tftp_path\tftp_cs_path\tftp_lbf_path\n')
        temp_metadata.write(
            'QTS000001\tQTD000001\tAlasoo_2018\tmacrophage_naive\tCL_0000235\tmacrophage\tnaive\t84\texon\thttp://example.com\thttp://example.com\thttp://example.com\n')
        temp_metadata_path = temp_metadata.name

    with tempfile.NamedTemporaryFile(prefix='IGVFFI0000TEST.', suffix='.tsv.gz', delete=False) as temp_file:
        with gzip.open(temp_file.name, 'wt') as f:
            f.write(
                'molecular_trait_id\tgene_id\tcs_id\tvariant\trsid\tcs_size\tpip\tpvalue\tbeta\tse\tz\tcs_min_r2\tregion\n')
            f.write('1:111139666:111140038:clu_35622_+\tENSG00000156171\t1:111139666:111140038:clu_35622_+_L1\tchr1_111108395_A_G\trs1583746\t4\t0.0680237702993137\t6.38809e-23\t-1.26169\t0.0859151\t-15.6241987461368\t0.948125027936558\tchr1:110138815-112138815\n')
        temp_file_path = temp_file.name

    try:
        with patch.object(EQTLCatalog, 'METADATA_PATH', temp_metadata_path):
            adapter = EQTLCatalog(filepath=temp_file_path,
                                  label='qtl',
                                  writer=writer,
                                  validate=True)
            adapter.process_file()

        mock_file_fileset_splice_qtl.assert_called_once_with('IGVFFI0000TEST')
        first_item = json.loads(writer.contents[0])
        assert len(writer.contents) > 0
        assert first_item['method'] == 'spliceQTL'
        assert first_item['label'] == 'spliceQTL'
        assert first_item['files_filesets'] == 'files_filesets/IGVFFI0000TEST'
        assert 'intron_chr' in first_item
        assert 'intron_start' in first_item
        assert 'intron_end' in first_item
        assert first_item['intron_chr'] == '1'
        assert first_item['intron_start'] == 111139666
        assert first_item['intron_end'] == 111140038
    finally:
        os.unlink(temp_file_path)
        os.unlink(temp_metadata_path)


@patch('adapters.eqtl_catalog_adapter.requests.get')
@patch('adapters.helpers.get_seqrepo')
@patch('adapters.eqtl_catalog_adapter.GeneValidator')
def test_eqtl_catalog_adapter_skips_edge_when_variant_not_loaded(mock_gene_validator, mock_get_seqrepo, mock_request, mock_file_fileset_eqtl, mock_bulk_check_variants):
    """A variant that isn't already in the variants collection must be
    skipped, not turned into a dangling edge."""
    mock_portal_aliases(mock_request)
    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = True
    mock_gene_validator.return_value = mock_validator_instance
    mock_bulk_check_variants.side_effect = None
    mock_bulk_check_variants.return_value = set()

    writer = SpyWriter()

    with tempfile.NamedTemporaryFile(prefix='IGVFFI0000TEST.', suffix='.tsv.gz', delete=False) as temp_file:
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

        assert len(writer.contents) == 0
    finally:
        os.unlink(temp_file_path)


def test_eqtl_catalog_adapter_variants_label_creates_missing_variant(mocker):
    """label='variants' should create a variant node for a valid variant
    that isn't already in the variants collection."""
    # build_variant_id() calls get_seqrepo() unconditionally, even for simple SNVs that
    # don't end up needing it - without this mock, environments without a real SeqRepo
    # install (e.g. CI) raise there, which process_variant_chunk silently catches and
    # treats as "skip this row", making the test fail with an empty writer instead of
    # erroring loudly.
    mock_seqrepo = MagicMock()
    mocker.patch('adapters.helpers.get_seqrepo', return_value=mock_seqrepo)
    mock_bulk_check_variants = mocker.patch(
        'adapters.eqtl_catalog_adapter.bulk_check_variants_in_arangodb')
    mock_bulk_check_variants.return_value = set()
    mock_load_variant = mocker.patch(
        'adapters.eqtl_catalog_adapter.load_variant')
    mock_load_variant.return_value = ({
        '_key': 'NC_000001.11:108004886:G:T',
        'name': 'NC_000001.11:108004886:G:T',
        'chr': 'chr1',
        'pos': 108004886,
        'ref': 'G',
        'alt': 'T',
        'variation_type': 'SNP',
        'spdi': 'NC_000001.11:108004886:G:T',
        'hgvs': 'fake_hgvs',
        'organism': 'Homo sapiens',
    }, None)

    writer = SpyWriter()

    with tempfile.NamedTemporaryFile(prefix='IGVFFI0000TEST.', suffix='.tsv.gz', delete=False) as temp_file:
        with gzip.open(temp_file.name, 'wt') as f:
            f.write(
                'molecular_trait_id\tgene_id\tcs_id\tvariant\trsid\tcs_size\tpip\tpvalue\tbeta\tse\tz\tcs_min_r2\tregion\n')
            f.write('ENSG00000230489\tENSG00000230489\tENSG00000230489_L1\tchr1_108004887_G_T\trs1936009\t53\t0.0197781278649429\t7.46541e-09\t0.767387\t0.116543\t7.19210214446939\t0.945192225726688\tchr1:106964443-108964443\n')
        temp_file_path = temp_file.name

    try:
        adapter = EQTLCatalog(filepath=temp_file_path,
                              label='variants',
                              writer=writer,
                              validate=True)
        adapter.process_file()

        non_empty_contents = [
            content for content in writer.contents if content.strip()]
        assert len(non_empty_contents) == 1
        item = json.loads(non_empty_contents[0])
        assert item['_key'] == 'NC_000001.11:108004886:G:T'
        assert item['source'] == 'EBI'
        assert item['source_url'] == EQTLCatalog.VARIANTS_SOURCE_URL
    finally:
        os.unlink(temp_file_path)


@patch('adapters.eqtl_catalog_adapter.requests.get')
def test_eqtl_catalog_adapter_no_metadata_found(mock_request, mock_file_fileset_eqtl):
    """Test error when no metadata is found for dataset"""
    mock_portal_aliases(mock_request, dataset_id='UNKNOWN')
    writer = SpyWriter()

    with tempfile.NamedTemporaryFile(prefix='IGVFFI0000TEST.', suffix='.tsv.gz', delete=False) as temp_file:
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
