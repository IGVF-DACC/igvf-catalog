import json
import pytest
from adapters.SEM_prediction_adapter import SEMPred
from adapters.writer import SpyWriter
from unittest.mock import patch

# real uniprot -> ENSP mapping for P20226 (TBP), used by the sample prediction file
SAMPLE_PROTEIN_MAP = {
    'P20226': ['ENSP00000230354', 'ENSP00000375942', 'ENSP00000442132']
}


# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test
@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.SEM_prediction_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'method': 'SEMVAR',
            'class': 'prediction',
            'samples': None,
            'simple_sample_summaries': None
        }
        yield mock_get_file_fileset


@pytest.fixture
def mock_protein_map():
    """Fixture to mock get_protein_map_from_arangodb so ArangoDB is not required."""
    with patch('adapters.protein_map.get_protein_map_from_arangodb') as mock_get_protein_map:
        mock_get_protein_map.return_value = SAMPLE_PROTEIN_MAP
        yield mock_get_protein_map


@pytest.fixture
def mock_bulk_check_variants():
    """Mock bulk_check_variants_in_arangodb. Defaults to treating every
    computed variant id as already loaded, so tests that aren't specifically
    exercising the existence check still see edges emitted; override
    .side_effect/.return_value in a test to exercise the skip path."""
    with patch('adapters.SEM_prediction_adapter.bulk_check_variants_in_arangodb') as mock_check:
        mock_check.side_effect = lambda variant_ids, **kwargs: set(
            variant_ids)
        yield mock_check


def test_sem_pred_adapter(mock_file_fileset, mock_protein_map, mock_bulk_check_variants):
    writer = SpyWriter()
    adapter = SEMPred(filepath='./samples/SEM/SEM_prediction_file.tsv.gz', sem_provenance_path='./samples/SEM/provenance_file.tsv.gz',
                      label='sem_predicted_asb', writer=writer, validate=True)
    adapter.process_file()
    mock_protein_map.assert_called_once_with(
        field='uniprot_ids',
        organism='Homo sapiens',
        dbxref_name=None,
    )
    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert '_key' in first_item
    assert '_from' in first_item
    assert '_to' in first_item
    assert first_item['_to'] == 'proteins/ENSP00000230354'
    assert 'motif' in first_item
    assert 'ref_seq_context' in first_item
    assert 'alt_seq_context' in first_item
    assert 'ref_score' in first_item
    assert 'alt_score' in first_item
    assert 'variant_effect_score' in first_item
    assert 'SEMpl_annotation' in first_item
    assert 'SEMpl_baseline' in first_item
    assert 'files_filesets' in first_item
    assert 'biological_process' in first_item
    assert 'source' in first_item
    assert 'source_url' in first_item
    assert first_item['label'] == 'predicted allele-specific binding'
    assert first_item['biological_process'] == 'ontology_terms/GO_0051101'
    assert first_item['name'] == 'modulates binding of'
    assert first_item['inverse_name'] == 'binding modulated by'
    assert first_item['biosample_term'] is None
    assert first_item['biological_context'] is None
    assert first_item['method'] == 'SEMVAR'
    assert first_item['class'] == 'prediction'


def test_sem_pred_adapter_invalid_label():
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: sem_predicted_asb, variants'):
        SEMPred(filepath='./samples/SEM/SEM_prediction_file.tsv.gz', sem_provenance_path='./samples/SEM/provenance_file.tsv.gz',
                label='invalid_label', writer=writer)


def p():
    adapter = SEMPred(filepath='./samples/SEM/SEM_prediction_file.tsv.gz',
                      sem_provenance_path='./samples/SEM/provenance_file.tsv.gz')
    adapter.load_tf_id_mapping()
    assert hasattr(adapter, 'tf_id_mapping')
    assert isinstance(adapter.tf_id_mapping, dict)
    assert len(adapter.tf_id_mapping) > 0


def test_sem_pred_adapter_binding_effect_filtering(mock_file_fileset, mock_protein_map, mock_bulk_check_variants):
    writer = SpyWriter()
    adapter = SEMPred(filepath='./samples/SEM/SEM_prediction_file.tsv.gz', sem_provenance_path='./samples/SEM/provenance_file.tsv.gz',
                      label='sem_predicted_asb', writer=writer)
    adapter.process_file()
    first_item = json.loads(writer.contents[0])
    assert first_item['SEMpl_annotation'] in SEMPred.BINDING_EFFECT_LIST


def test_sem_pred_adapter_skips_edge_when_variant_not_loaded(mock_file_fileset, mock_protein_map, mock_bulk_check_variants):
    """A variant that isn't already in the variants collection must be
    skipped, not turned into a dangling edge."""
    mock_bulk_check_variants.side_effect = None
    mock_bulk_check_variants.return_value = set()
    writer = SpyWriter()
    adapter = SEMPred(filepath='./samples/SEM/SEM_prediction_file.tsv.gz', sem_provenance_path='./samples/SEM/provenance_file.tsv.gz',
                      label='sem_predicted_asb', writer=writer, validate=True)
    adapter.process_file()

    non_empty_contents = [
        content for content in writer.contents if content.strip()]
    assert len(non_empty_contents) == 0


def test_sem_pred_adapter_variants_label_creates_missing_variant(mock_file_fileset, mock_bulk_check_variants, mocker):
    """label='variants' should create a variant node for a valid variant
    that isn't already in the variants collection."""
    mock_load_variant = mocker.patch(
        'adapters.SEM_prediction_adapter.load_variant')
    mock_bulk_check_variants.side_effect = None
    mock_bulk_check_variants.return_value = set()
    mock_load_variant.return_value = ({
        '_key': 'NC_000010.11:10157:T:C',
        'name': 'NC_000010.11:10157:T:C',
        'chr': 'chr10',
        'pos': 10157,
        'ref': 'T',
        'alt': 'C',
        'variation_type': 'SNP',
        'spdi': 'NC_000010.11:10157:T:C',
        'hgvs': 'fake_hgvs',
        'organism': 'Homo sapiens',
    }, None)

    writer = SpyWriter()
    adapter = SEMPred(filepath='./samples/SEM/SEM_prediction_file.tsv.gz', sem_provenance_path='./samples/SEM/provenance_file.tsv.gz',
                      label='variants', writer=writer, validate=True)
    adapter.process_file()

    non_empty_contents = [
        content for content in writer.contents if content.strip()]
    assert len(non_empty_contents) >= 1
    item = json.loads(non_empty_contents[0])
    assert item['source'] == SEMPred.SOURCE
    assert item['files_filesets'] == f'files_filesets/{adapter.file_accession}'


def test_validate_doc_invalid():
    writer = SpyWriter()
    adapter = SEMPred(filepath='./samples/SEM/SEM_prediction_file.tsv.gz',
                      sem_provenance_path='./samples/SEM/provenance_file.tsv.gz', label='sem_predicted_asb', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
