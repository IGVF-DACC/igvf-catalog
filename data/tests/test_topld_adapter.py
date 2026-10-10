import json
from unittest.mock import patch
from adapters.topld_adapter import TopLD
from adapters.writer import SpyWriter
import pytest


@pytest.fixture
def mock_bulk_check_variants():
    """Mock bulk_check_variants_in_arangodb. Defaults to treating every
    computed variant id as already loaded, so tests that aren't specifically
    exercising the existence check still see edges emitted; override
    .side_effect/.return_value in a test to exercise the skip path."""
    with patch('adapters.topld_adapter.bulk_check_variants_in_arangodb') as mock_check:
        mock_check.side_effect = lambda variant_ids, **kwargs: set(
            variant_ids)
        yield mock_check


def test_topld_adapter_initialization():
    writer = SpyWriter()
    adapter = TopLD(filepath='./samples/topld_sample.csv',
                    annotation_filepath='./samples/topld_info_annotation.csv',
                    chr='chr22',
                    ancestry='SAS',
                    writer=writer)

    assert adapter.filepath == './samples/topld_sample.csv'
    assert adapter.annotation_filepath == './samples/topld_info_annotation.csv'
    assert adapter.chr == 'chr22'
    assert adapter.ancestry == 'SAS'
    assert adapter.label == 'topld_linkage_disequilibrium'
    assert adapter.writer == writer


def test_topld_adapter_process_file(mocker, mock_bulk_check_variants):
    mocker.patch('adapters.topld_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    adapter = TopLD(filepath='./samples/topld_sample.csv',
                    annotation_filepath='./samples/topld_info_annotation.csv',
                    chr='chr22',
                    ancestry='SAS',
                    writer=writer,
                    validate=True)

    adapter.process_file()

    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])

    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert 'chr' in first_item
    # regression test: TopLD's +/-corr column is + for positive correlation, - for
    # negative; positive_corr used to be named "negated" while keeping the same `== '+'`
    # comparison, so it was true for positive correlation despite the name implying the
    # opposite.
    assert 'positive_corr' in first_item
    assert first_item['positive_corr'] is True
    assert 'variant_1_base_pair' in first_item
    assert 'variant_2_base_pair' in first_item
    assert 'variant_1_rsid' in first_item
    assert 'variant_2_rsid' in first_item
    assert 'r2' in first_item
    assert 'd_prime' in first_item
    assert 'ancestry' in first_item
    assert 'label' in first_item
    assert 'name' in first_item
    assert 'inverse_name' in first_item
    assert 'source' in first_item
    assert 'source_url' in first_item

    assert first_item['_key'] == 'fake_variant_id_C:A_fake_variant_id_A:G_SAS'
    assert first_item['chr'] == 'chr22'
    assert first_item['ancestry'] == 'SAS'
    assert first_item['label'] == 'linkage disequilibrium'
    assert first_item['name'] == 'correlated with'
    assert first_item['inverse_name'] == 'correlated with'
    assert first_item['source'] == 'TopLD'
    assert first_item['source_url'] == 'http://topld.genetics.unc.edu/'


def test_topld_adapter_skips_edge_when_variant_not_loaded(mocker, mock_bulk_check_variants):
    """An edge must be skipped, not emitted with a dangling reference, when
    either endpoint variant isn't already in the variants collection."""
    mocker.patch('adapters.topld_adapter.build_variant_id',
                 return_value='fake_variant_id')
    mock_bulk_check_variants.side_effect = None
    mock_bulk_check_variants.return_value = set()
    writer = SpyWriter()
    adapter = TopLD(filepath='./samples/topld_sample.csv',
                    annotation_filepath='./samples/topld_info_annotation.csv',
                    chr='chr22',
                    ancestry='SAS',
                    writer=writer,
                    validate=True)

    adapter.process_file()

    non_empty_contents = [
        content for content in writer.contents if content.strip()]
    assert len(non_empty_contents) == 0


def test_topld_adapter_variants_label_creates_missing_variant(mocker, mock_bulk_check_variants):
    """label='variants' should create a variant node for a valid variant
    that isn't already in the variants collection."""
    mocker.patch('adapters.topld_adapter.build_variant_id',
                 return_value='fake_variant_id')
    mock_load_variant = mocker.patch('adapters.topld_adapter.load_variant')
    mock_bulk_check_variants.side_effect = None
    mock_bulk_check_variants.return_value = set()
    mock_load_variant.return_value = ({
        '_key': 'fake_variant_id',
        'name': 'fake_variant_id',
        'chr': 'chr22',
        'pos': 8549508,
        'ref': 'C',
        'alt': 'A',
        'variation_type': 'SNP',
        'spdi': 'fake_variant_id',
        'hgvs': 'fake_hgvs',
        'organism': 'Homo sapiens',
    }, None)

    writer = SpyWriter()
    adapter = TopLD(filepath='./samples/topld_sample.csv',
                    annotation_filepath='./samples/topld_info_annotation.csv',
                    chr='chr22',
                    ancestry='SAS',
                    label='variants',
                    writer=writer,
                    validate=True)
    adapter.process_file()

    non_empty_contents = [
        content for content in writer.contents if content.strip()]
    # Same mocked variant id is produced for every row - written_variant_keys
    # must dedupe it down to a single node.
    assert len(non_empty_contents) == 1
    item = json.loads(non_empty_contents[0])
    assert item['_key'] == 'fake_variant_id'
    assert item['source'] == TopLD.SOURCE
    assert item['source_url'] == TopLD.SOURCE_URL


def test_topld_adapter_process_annotations(mocker):
    mocker.patch('adapters.topld_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    adapter = TopLD(filepath='./samples/topld_sample.csv',
                    annotation_filepath='./samples/topld_info_annotation.csv',
                    chr='chr22',
                    ancestry='SAS',
                    writer=writer)

    adapter.process_annotations()

    assert len(adapter.ids) > 0
    first_key = next(iter(adapter.ids))
    first_value = adapter.ids[first_key]

    assert 'rsid' in first_value
    assert 'variant_id' in first_value
    assert first_value['variant_id'].startswith('variants/')


def test_topld_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = TopLD(filepath='./samples/topld_sample.csv',
                    annotation_filepath='./samples/topld_info_annotation.csv',
                    chr='chr22',
                    ancestry='SAS',
                    writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
