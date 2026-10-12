import json
from unittest.mock import patch
import pytest

from adapters.AFGR_sqtl_adapter import AFGRSQtl
from adapters.writer import SpyWriter


def mock_igvf_metadata(mock_request):
    mock_request.return_value = {
        'class': 'observed data',
        'method': 'spliceQTL'
    }


@pytest.fixture
def mock_bulk_check_variants():
    """Mock bulk_check_variants_in_arangodb. Defaults to treating every
    computed variant id as already loaded, so tests that aren't specifically
    exercising the existence check still see edges emitted; override
    .side_effect/.return_value in a test to exercise the skip path."""
    with patch('adapters.AFGR_sqtl_adapter.bulk_check_variants_in_arangodb') as mock_check:
        mock_check.side_effect = lambda variant_ids, **kwargs: set(
            variant_ids)
        yield mock_check


@patch('adapters.AFGR_sqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_sqtl_adapter_AFGR_sqtl(mock_request, mock_bulk_check_variants, mocker):
    mock_igvf_metadata(mock_request)
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
        assert len(first_item) == 21
        assert first_item['intron_chr'].startswith('chr')

        # regression test: intron_start/intron_end are range-filterable (ZKD index) and
        # the API's completeQtlsFormat expects numbers; they used to be written as raw
        # strings from intron_id.split(':'), which both broke numeric range filtering and
        # caused "Output validation failed" once the real output schema was enforced.

        assert isinstance(first_item['intron_start'], int)
        assert isinstance(first_item['intron_end'], int)


def test_AFGR_sqtl_adapter_AFGR_sqtl_term_invalid_label(mocker):
    writer = SpyWriter()
    with pytest.raises(ValueError):
        adapter = AFGRSQtl(filepath='./samples/AFGR/sorted.all.AFR.Meta.sQTL.example.txt.gz',
                           label='invalid_label', writer=writer, validate=True)


@patch('adapters.AFGR_sqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_sqtl_adapter_AFGR_sqtl_term_validate_doc_invalid(mock_request, mocker):
    mock_igvf_metadata(mock_request)
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


@patch('adapters.AFGR_sqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_sqtl_adapter_AFGR_sqtl_invalid_gene_id(mock_request, mock_bulk_check_variants, mocker):
    mock_igvf_metadata(mock_request)
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


@patch('adapters.AFGR_sqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_sqtl_adapter_skips_edge_when_variant_not_loaded(mock_request, mock_bulk_check_variants, mocker):
    """A variant that isn't already in the variants collection must be
    skipped, not turned into a dangling edge."""
    mock_igvf_metadata(mock_request)
    mocker.patch('adapters.AFGR_sqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    mock_bulk_check_variants.side_effect = None
    mock_bulk_check_variants.return_value = set()
    writer = SpyWriter()
    with patch('adapters.AFGR_sqtl_adapter.GeneValidator') as MockGeneValidator:
        mock_validator_instance = MockGeneValidator.return_value
        mock_validator_instance.validate.return_value = True
        adapter = AFGRSQtl(filepath='./samples/AFGR/sorted.all.AFR.Meta.sQTL.example.txt.gz',
                           label='AFGR_sqtl', writer=writer, validate=True)
        adapter.process_file()
        assert len(writer.contents) == 0


@patch('adapters.AFGR_sqtl_adapter.load_variant')
@patch('adapters.AFGR_sqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_sqtl_adapter_variants_label_creates_missing_variant(mock_request, mock_load_variant, mock_bulk_check_variants, mocker):
    """label='variants' should create a variant node for a valid variant
    that isn't already in the variants collection."""
    mock_igvf_metadata(mock_request)
    mocker.patch('adapters.AFGR_sqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    mock_bulk_check_variants.side_effect = None
    mock_bulk_check_variants.return_value = set()
    mock_load_variant.return_value = ({
        '_key': 'fake_variant_id',
        'name': 'fake_variant_id',
        'chr': 'chr1',
        'pos': 88337,
        'ref': 'G',
        'alt': 'A',
        'variation_type': 'SNP',
        'spdi': 'fake_variant_id',
        'hgvs': 'fake_hgvs',
        'organism': 'Homo sapiens',
    }, None)

    writer = SpyWriter()
    adapter = AFGRSQtl(filepath='./samples/AFGR/sorted.all.AFR.Meta.sQTL.example.txt.gz',
                       label='variants', writer=writer, validate=True)
    adapter.process_file()

    non_empty_contents = [
        content for content in writer.contents if content.strip()]
    # Same mocked variant id is produced for every row - written_variant_keys
    # must dedupe it down to a single node.
    assert len(non_empty_contents) == 1
    item = json.loads(non_empty_contents[0])
    assert item['_key'] == 'fake_variant_id'
    assert item['source'] == AFGRSQtl.SOURCE
    assert item['source_url'] == AFGRSQtl.SOURCE_URL


@patch('adapters.AFGR_sqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_sqtl_adapter_AFGR_sqtl_skip_alt_star(mock_request):
    """Test that deletion variants (alt='*') are skipped (covers lines 70-71)"""
    mock_igvf_metadata(mock_request)
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


@patch('adapters.AFGR_sqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_sqtl_adapter_no_gene_mapping(mock_request, mock_bulk_check_variants, mocker):
    """Test that introns without gene mapping are skipped (covers lines 78-79)"""
    mock_igvf_metadata(mock_request)
    writer = SpyWriter()

    # Mock build_variant_id to avoid SeqRepo dependency
    mocker.patch('adapters.AFGR_sqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')

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
