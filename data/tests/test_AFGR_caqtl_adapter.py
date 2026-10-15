import json

from adapters.AFGR_caqtl_adapter import AFGRCAQtl
from adapters.writer import SpyWriter
import pytest
from unittest.mock import patch


def mock_igvf_metadata(mock_request):
    mock_request.return_value = {
        'class': 'observed data',
        'method': 'caQTL'
    }


@pytest.fixture
def mock_bulk_check_variants():
    """Mock bulk_check_variants_in_arangodb. Defaults to treating every
    computed variant id as already loaded, so tests that aren't specifically
    exercising the existence check still see edges emitted; override
    .side_effect/.return_value in a test to exercise the skip path."""
    with patch('adapters.AFGR_caqtl_adapter.bulk_check_variants_in_arangodb') as mock_check:
        mock_check.side_effect = lambda variant_ids, **kwargs: set(
            variant_ids)
        yield mock_check


@patch('adapters.AFGR_caqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_caqtl_adapter_regulatory_region(mock_request):
    mock_igvf_metadata(mock_request)
    writer = SpyWriter()
    adapter = AFGRCAQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR.caQTL.example.txt.gz',
                        label='genomic_element', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) == 200
    assert len(first_item) == 10
    assert first_item['_key'] == 'accessible_dna_element_1_906596_907043_GRCh38_AFGR'
    assert first_item['method'] == 'caQTL'


@patch('adapters.AFGR_caqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_caqtl_adapter_AFGR_caqtl(mock_request, mock_bulk_check_variants, mocker):
    mock_igvf_metadata(mock_request)
    mocker.patch('adapters.AFGR_caqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    adapter = AFGRCAQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR.caQTL.example.txt.gz',
                        label='AFGR_caqtl', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) == 200
    assert len(first_item) == 16
    assert '_from' in first_item
    assert first_item['_key'] == 'fake_variant_id_accessible_dna_element_1_906596_907043_GRCh38_AFGR'
    assert first_item['method'] == 'caQTL'
    assert first_item['class'] == 'observed data'
    assert first_item['neg_log10_pvalue'] == 5.318140333513867


@patch('adapters.AFGR_caqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_caqtl_adapter_skips_edge_when_variant_not_loaded(mock_request, mock_bulk_check_variants, mocker):
    """A variant that isn't already in the variants collection must be
    skipped, not turned into a dangling edge."""
    mock_igvf_metadata(mock_request)
    mocker.patch('adapters.AFGR_caqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    mock_bulk_check_variants.side_effect = None
    mock_bulk_check_variants.return_value = set()

    writer = SpyWriter()
    adapter = AFGRCAQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR.caQTL.example.txt.gz',
                        label='AFGR_caqtl', writer=writer, validate=True)
    adapter.process_file()

    assert len(writer.contents) == 0


@patch('adapters.AFGR_caqtl_adapter.load_variant')
@patch('adapters.AFGR_caqtl_adapter.get_file_fileset_by_accession_in_arangodb')
def test_AFGR_caqtl_adapter_variants_label_creates_missing_variant(mock_request, mock_load_variant, mock_bulk_check_variants, mocker):
    """label='variants' should create a variant node for a valid variant
    that isn't already in the variants collection."""
    mock_igvf_metadata(mock_request)
    mocker.patch('adapters.AFGR_caqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    mock_bulk_check_variants.side_effect = None
    mock_bulk_check_variants.return_value = set()
    mock_load_variant.return_value = ({
        '_key': 'fake_variant_id',
        'name': 'fake_variant_id',
        'chr': 'chr1',
        'pos': 906595,
        'ref': 'A',
        'alt': 'T',
        'variation_type': 'SNP',
        'spdi': 'fake_variant_id',
        'hgvs': 'fake_hgvs',
        'organism': 'Homo sapiens',
    }, None)

    writer = SpyWriter()
    adapter = AFGRCAQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR.caQTL.example.txt.gz',
                        label='variants', writer=writer, validate=True)
    adapter.process_file()

    # Same mocked variant id is produced for every row - written_variant_keys
    # must dedupe it down to a single node.
    non_empty_contents = [
        content for content in writer.contents if content.strip()]
    assert len(non_empty_contents) == 1
    item = json.loads(non_empty_contents[0])
    assert item['_key'] == 'fake_variant_id'
    assert item['source'] == AFGRCAQtl.SOURCE
    assert item['source_url'] == AFGRCAQtl.SOURCE_URL
    assert item['files_filesets'] == 'files_filesets/sorted'


def test_AFGR_caqtl_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError):
        adapter = AFGRCAQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR.caQTL.example.txt.gz',
                            label='invalid_label', writer=writer, validate=True)


def test_AFGR_caqtl_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = AFGRCAQtl(filepath='./samples/AFGR/sorted.dist.hwe.af.AFR.caQTL.example.txt.gz',
                        label='AFGR_caqtl', writer=writer, validate=True)

    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
