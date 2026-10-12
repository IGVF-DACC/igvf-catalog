import json
from unittest.mock import patch

from adapters.AFGR_eqtl_adapter import AFGREQtl
from adapters.writer import SpyWriter
import pytest


def mock_igvf_metadata(mock_request):
    mock_request.return_value = {
        'class': 'observed data',
        'method': 'eQTL'
    }


@pytest.fixture
def mock_bulk_check_variants():
    """Mock bulk_check_variants_in_arangodb. Defaults to treating every
    computed variant id as already loaded, so tests that aren't specifically
    exercising the existence check still see edges emitted; override
    .side_effect/.return_value in a test to exercise the skip path."""
    with patch('adapters.AFGR_eqtl_adapter.bulk_check_variants_in_arangodb') as mock_check:
        mock_check.side_effect = lambda variant_ids, **kwargs: set(
            variant_ids)
        yield mock_check


@patch('adapters.AFGR_eqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_eqtl_adapter_AFGR_eqtl(mock_request, mock_bulk_check_variants, mocker):
    mock_igvf_metadata(mock_request)
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
        assert len(first_item) == 18
        assert first_item['inverse_name'] == 'expression modulated by'


@patch('adapters.AFGR_eqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_eqtl_adapter_key_includes_file_accession(mock_request, mock_bulk_check_variants, mocker):
    """Different file accessions must produce different edge keys for the same pair."""
    import hashlib
    mock_igvf_metadata(mock_request)
    mocker.patch('adapters.AFGR_eqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')

    with patch('adapters.AFGR_eqtl_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        writer_a = SpyWriter()
        adapter_a = AFGREQtl(
            filepath='./samples/AFGR/sorted.dist.hwe.af.AFR_META.eQTL.example.txt.gz',
            label='AFGR_eqtl',
            writer=writer_a,
            validate=False
        )
        adapter_a.file_accession = 'IGVFFIAAAA0001'
        adapter_a.process_file()

        writer_b = SpyWriter()
        adapter_b = AFGREQtl(
            filepath='./samples/AFGR/sorted.dist.hwe.af.AFR_META.eQTL.example.txt.gz',
            label='AFGR_eqtl',
            writer=writer_b,
            validate=False
        )
        adapter_b.file_accession = 'IGVFFIBBBB0002'
        adapter_b.process_file()

        key_a = json.loads(writer_a.contents[0])['_key']
        key_b = json.loads(writer_b.contents[0])['_key']
        assert key_a != key_b

        gene_id = json.loads(writer_a.contents[0])['_to'].split('/')[-1]
        expected_a = hashlib.sha256(
            ('fake_variant_id_' + gene_id + '_IGVFFIAAAA0001').encode()
        ).hexdigest()
        assert key_a == expected_a


def test_AFGR_eqtl_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError):
        adapter = AFGREQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR_META.eQTL.example.txt.gz',
                           label='invalid_label', writer=writer, validate=True)


def test_AFGR_eqtl_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = AFGREQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR_META.eQTL.example.txt.gz',
                       label='AFGR_eqtl', writer=writer, validate=True)

    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)


@patch('adapters.AFGR_eqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_eqtl_adapter_AFGR_eqtl_invalid_gene_id(mock_request, mock_bulk_check_variants, mocker):
    mock_igvf_metadata(mock_request)
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


@patch('adapters.AFGR_eqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_eqtl_adapter_skips_edge_when_variant_not_loaded(mock_request, mock_bulk_check_variants, mocker):
    """A variant that isn't already in the variants collection must be
    skipped, not turned into a dangling edge."""
    mock_igvf_metadata(mock_request)
    writer = SpyWriter()
    mocker.patch('adapters.AFGR_eqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    mock_bulk_check_variants.side_effect = None
    mock_bulk_check_variants.return_value = set()

    with patch('adapters.AFGR_eqtl_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True

        adapter = AFGREQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR_META.eQTL.example.txt.gz',
                           label='AFGR_eqtl', writer=writer, validate=True)
        adapter.process_file()
        assert len(writer.contents) == 0


@patch('adapters.AFGR_eqtl_adapter.load_variant')
@patch('adapters.AFGR_eqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_eqtl_adapter_variants_label_creates_missing_variant(mock_request, mock_load_variant, mock_bulk_check_variants, mocker):
    """label='variants' should create a variant node for a valid variant
    that isn't already in the variants collection."""
    mock_igvf_metadata(mock_request)
    writer = SpyWriter()
    mocker.patch('adapters.AFGR_eqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    mock_bulk_check_variants.side_effect = None
    mock_bulk_check_variants.return_value = set()
    mock_load_variant.return_value = ({
        '_key': 'fake_variant_id',
        'name': 'fake_variant_id',
        'chr': 'chr1',
        'pos': 16102,
        'ref': 'T',
        'alt': 'G',
        'variation_type': 'SNP',
        'spdi': 'fake_variant_id',
        'hgvs': 'fake_hgvs',
        'organism': 'Homo sapiens',
    }, None)

    adapter = AFGREQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR_META.eQTL.example.txt.gz',
                       label='variants', writer=writer, validate=True)
    adapter.process_file()

    non_empty_contents = [
        content for content in writer.contents if content.strip()]
    # Same mocked variant id is produced for every row - written_variant_keys
    # must dedupe it down to a single node.
    assert len(non_empty_contents) == 1
    item = json.loads(non_empty_contents[0])
    assert item['_key'] == 'fake_variant_id'
    assert item['source'] == AFGREQtl.SOURCE
    assert item['source_url'] == AFGREQtl.SOURCE_URL


@patch('adapters.AFGR_eqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_eqtl_adapter_deletion_variant_skipped(mock_request):
    """Test that deletion variants (alt='*') are skipped (covers line 64)"""
    mock_igvf_metadata(mock_request)
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
