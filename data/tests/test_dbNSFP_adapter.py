import json
from unittest.mock import patch
from adapters.dbNSFP_adapter import DbNSFP
from adapters.writer import SpyWriter
import pytest


@pytest.fixture
def mock_bulk_check_variants():
    """Mock bulk_check_variants_in_arangodb. Defaults to treating every
    computed variant id as already loaded, so tests that aren't specifically
    exercising the existence check still see edges emitted; override
    .side_effect/.return_value in a test to exercise the skip path."""
    with patch('adapters.dbNSFP_adapter.bulk_check_variants_in_arangodb') as mock_check:
        mock_check.side_effect = lambda variant_ids, **kwargs: set(
            variant_ids)
        yield mock_check


def test_dbNSFP_adapter_coding_variants(mocker):
    mocker.patch('adapters.dbNSFP_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    adapter = DbNSFP(
        filepath='./samples/dbNSFP4.5a_variant.chrY_sample', writer=writer, validate=True)
    adapter.process_file()

    assert len(writer.contents) > 1
    first_item = json.loads(writer.contents[0])

    assert '_key' in first_item
    assert 'name' in first_item
    assert 'gene_name' in first_item
    assert 'transcript_id' in first_item
    assert 'source' in first_item
    assert first_item['source'] == 'dbNSFP 5.1a'


def test_dbNSFP_adapter_variants_coding_variants(mock_bulk_check_variants, mocker):
    mocker.patch('adapters.dbNSFP_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()

    adapter = DbNSFP(filepath='./samples/dbNSFP4.5a_variant.chrY_sample',
                     label='variants_coding_variants', writer=writer, validate=True)
    adapter.process_file()

    assert len(writer.contents) > 1
    first_item = json.loads(writer.contents[0])

    assert '_from' in first_item
    assert '_to' in first_item
    assert 'name' in first_item
    assert 'inverse_name' in first_item
    assert 'source' in first_item
    assert first_item['source'] == 'dbNSFP 5.1a'


def test_dbNSFP_adapter_skips_edge_when_variant_not_loaded(mock_bulk_check_variants, mocker):
    """A variant that isn't already in the variants collection must be
    skipped, not turned into a dangling edge."""
    mocker.patch('adapters.dbNSFP_adapter.build_variant_id',
                 return_value='fake_variant_id')
    mock_bulk_check_variants.side_effect = None
    mock_bulk_check_variants.return_value = set()
    writer = SpyWriter()

    adapter = DbNSFP(filepath='./samples/dbNSFP4.5a_variant.chrY_sample',
                     label='variants_coding_variants', writer=writer, validate=True)
    adapter.process_file()

    non_empty_contents = [
        content for content in writer.contents if content.strip()]
    assert len(non_empty_contents) == 0


def test_dbNSFP_adapter_variants_label_creates_missing_variant(mock_bulk_check_variants, mocker):
    """label='variants' should create a variant node for a valid variant
    that isn't already in the variants collection."""
    mocker.patch('adapters.dbNSFP_adapter.build_variant_id',
                 return_value='fake_variant_id')
    mock_load_variant = mocker.patch('adapters.dbNSFP_adapter.load_variant')
    mock_bulk_check_variants.side_effect = None
    mock_bulk_check_variants.return_value = set()
    mock_load_variant.return_value = ({
        '_key': 'fake_variant_id',
        'name': 'fake_variant_id',
        'chr': 'chrY',
        'pos': 2786988,
        'ref': 'C',
        'alt': 'A',
        'variation_type': 'SNP',
        'spdi': 'fake_variant_id',
        'hgvs': 'fake_hgvs',
        'organism': 'Homo sapiens',
    }, None)
    writer = SpyWriter()

    adapter = DbNSFP(filepath='./samples/dbNSFP4.5a_variant.chrY_sample',
                     label='variants', writer=writer, validate=True)
    adapter.process_file()

    non_empty_contents = [
        content for content in writer.contents if content.strip()]
    # Same mocked variant id is produced for every row - written_variant_keys
    # must dedupe it down to a single node.
    assert len(non_empty_contents) == 1
    item = json.loads(non_empty_contents[0])
    assert item['_key'] == 'fake_variant_id'
    assert item['source'] == DbNSFP.SOURCE
    assert item['source_url'] == DbNSFP.SOURCE_URL
def test_dbNSFP_adapter_multiple_records():
    adapter = DbNSFP(filepath='./samples/dbNSFP4.5a_variant.chrY_sample')
    data_line = ['Y', '2786989', 'C', 'A', 'X', 'Y', '.', 'Y', '2655030', 'Y', '2715030', '205;206', 'SRY;SRY',
                 'ENSG00000184895;ENSG00000184895', 'ENST00000383070;ENST00000383070', 'ENSP00000372547;ENSP00000372547']

    assert adapter.multiple_records(data_line) == True


def test_dbNSFP_adapter_breakdown_line():
    adapter = DbNSFP(filepath='./samples/dbNSFP4.5a_variant.chrY_sample')
    original_data_line = ['Y', '2786989', 'C', 'A', 'X', 'Y', '.', 'Y', '2655030', 'Y', '2715030', '205;206', 'SRY;SRY',
                          'ENSG00000184895;ENSG00000184895', 'ENST00000383070;ENST00000383070', 'ENSP00000372547;ENSP00000372547']

    broken_down_lines = adapter.breakdown_line(original_data_line)

    assert len(broken_down_lines) == 2
    assert broken_down_lines[0][11] == '205'
    assert broken_down_lines[1][11] == '206'
    assert broken_down_lines[0][12] == 'SRY'
    assert broken_down_lines[1][12] == 'SRY'


def test_dbNSFP_adapter_initialization():
    adapter = DbNSFP(filepath='./samples/dbNSFP4.5a_variant.chrY_sample',
                     label='variants_coding_variants')

    assert adapter.filepath == './samples/dbNSFP4.5a_variant.chrY_sample'
    assert adapter.label == 'variants_coding_variants'


def test_dbNSFP_adapter_validate_doc_invalid():
    writer = SpyWriter()
    adapter = DbNSFP(filepath='./samples/dbNSFP4.5a_variant.chrY_sample',
                     label='variants_coding_variants', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
