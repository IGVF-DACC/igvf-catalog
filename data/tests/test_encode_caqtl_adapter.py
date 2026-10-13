import json
import pytest
from adapters.encode_caqtl_adapter import CAQtl
from adapters.writer import SpyWriter
from unittest.mock import patch


# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test
@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.encode_caqtl_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'caQTL',
            'class': 'observed data'
        }
        yield mock_get_file_fileset


@pytest.mark.external_dependency
def test_caqtl_adapter_regulatory_region(mock_file_fileset):
    writer = SpyWriter()
    adapter = CAQtl(filepath='./samples/ENCFF103XRK.sample.bed',
                    source='PMID:34017130', label='genomic_element', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert 'chr' in first_item
    assert 'start' in first_item
    assert 'end' in first_item
    assert first_item['type'] == 'accessible dna elements'


@pytest.fixture
def mock_bulk_check_variants():
    """Mock bulk_check_variants_in_arangodb. Defaults to treating every
    computed variant id as already loaded, so tests that aren't specifically
    exercising the existence check still see edges emitted; override
    .side_effect/.return_value in a test to exercise the skip path."""
    with patch('adapters.encode_caqtl_adapter.bulk_check_variants_in_arangodb') as mock_check:
        mock_check.side_effect = lambda variant_ids, **kwargs: set(
            variant_ids)
        yield mock_check


@pytest.mark.external_dependency
def test_caqtl_adapter_encode_caqtl(mocker, mock_file_fileset, mock_bulk_check_variants):
    mocker.patch('adapters.encode_caqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    writer = SpyWriter()
    adapter = CAQtl(filepath='./samples/ENCFF103XRK.sample.bed',
                    source='PMID:34017130', label='encode_caqtl', writer=writer, validate=True)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['label'] == 'caQTL'
    assert first_item['name'] == 'modulates accessibility of'
    assert first_item['inverse_name'] == 'accessibility modulated by'
    assert first_item['method'] == 'caQTL'
    assert first_item['class'] == 'observed data'


@pytest.mark.external_dependency
def test_caqtl_adapter_skips_edge_when_variant_not_loaded(mocker, mock_file_fileset, mock_bulk_check_variants):
    """A variant that isn't already in the variants collection must be
    skipped, not turned into a dangling edge."""
    mocker.patch('adapters.encode_caqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    mock_bulk_check_variants.side_effect = None
    mock_bulk_check_variants.return_value = set()
    writer = SpyWriter()
    adapter = CAQtl(filepath='./samples/ENCFF103XRK.sample.bed',
                    source='PMID:34017130', label='encode_caqtl', writer=writer, validate=True)
    adapter.process_file()
    assert len(writer.contents) == 0


@pytest.mark.external_dependency
def test_caqtl_adapter_variants_label_creates_missing_variant(mocker, mock_file_fileset, mock_bulk_check_variants):
    """label='variants' should create a variant node for a valid variant
    that isn't already in the variants collection."""
    mocker.patch('adapters.encode_caqtl_adapter.build_variant_id',
                 return_value='fake_variant_id')
    mock_load_variant = mocker.patch(
        'adapters.encode_caqtl_adapter.load_variant')
    mock_bulk_check_variants.side_effect = None
    mock_bulk_check_variants.return_value = set()
    mock_load_variant.return_value = ({
        '_key': 'fake_variant_id',
        'name': 'fake_variant_id',
        'chr': 'chr1',
        'pos': 766454,
        'ref': 'T',
        'alt': 'C',
        'variation_type': 'SNP',
        'spdi': 'fake_variant_id',
        'hgvs': 'fake_hgvs',
        'organism': 'Homo sapiens',
    }, None)
    writer = SpyWriter()
    adapter = CAQtl(filepath='./samples/ENCFF103XRK.sample.bed',
                    source='PMID:34017130', label='variants', writer=writer, validate=True)
    adapter.process_file()

    non_empty_contents = [
        content for content in writer.contents if content.strip()]
    # Same mocked variant id is produced for every row - written_variant_keys
    # must dedupe it down to a single node.
    assert len(non_empty_contents) == 1
    item = json.loads(non_empty_contents[0])
    assert item['_key'] == 'fake_variant_id'
    assert item['source'] == 'ENCODE'
    assert item['files_filesets'] == 'files_filesets/ENCFF103XRK'


def test_caqtl_adapter_invalid_label(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: genomic_element, encode_caqtl, variants'):
        CAQtl(filepath='./samples/ENCFF103XRK.sample.bed',
              source='PMID:34017130', label='invalid_label', writer=writer)


def test_caqtl_adapter_initialization(mock_file_fileset):
    writer = SpyWriter()
    for label in CAQtl.ALLOWED_LABELS:
        adapter = CAQtl(filepath='./samples/ENCFF103XRK.sample.bed',
                        source='PMID:34017130', label=label, writer=writer)
        assert adapter.filepath == './samples/ENCFF103XRK.sample.bed'
        assert adapter.label == label
        assert adapter.source == 'PMID:34017130'
        assert adapter.writer == writer
        assert adapter.file_accession == 'ENCFF103XRK'


def test_caqtl_adapter_validate_doc_invalid(mock_file_fileset):
    writer = SpyWriter()
    adapter = CAQtl(filepath='./samples/ENCFF103XRK.sample.bed',
                    source='PMID:34017130', label='encode_caqtl', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
