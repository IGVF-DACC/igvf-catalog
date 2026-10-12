import json
import pytest
from adapters.BlueSTARR_variants_biosamples_adapter import BlueSTARRVariantBiosample
from adapters.writer import SpyWriter
from unittest.mock import patch, mock_open

FILE_ACCESSION = 'IGVFFI5288RAAV'
FILEPATH = f'./samples/bluestarr.{FILE_ACCESSION}.tsv'

mock_bed_data = (
    'chr10\t100005234\t100005491\t0.126\tNC_000010.11:100005302:A:C\n'
)


# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test
@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.BlueSTARR_variants_biosamples_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        mock_get_file_fileset.return_value = {
            'simple_sample_summaries': ['K562'],
            'samples': ['ontology_terms/EFO_0002067'],
            'method': 'BlueSTARR',
            'class': 'prediction'
        }
        yield mock_get_file_fileset


# mock load_variant to avoid repeated setup
@pytest.fixture
def mock_load_variant():
    """Fixture to mock load_variant function."""
    with patch('adapters.BlueSTARR_variants_biosamples_adapter.load_variant') as mock_load:
        mock_load.return_value = ({
            '_key': 'NC_000010.11:100005302:A:C',
            'name': 'NC_000010.11:100005302:A:C',
            'chr': 'chr10',
            'pos': 100005302,
            'ref': 'A',
            'alt': 'C',
            'variation_type': 'SNP',
            'spdi': 'NC_000010.11:100005302:A:C',
            'hgvs': 'NC_000010.11:g.100005303A>C',
            'organism': 'Homo sapiens'
        }, None)
        yield mock_load


# mock build_variant_id to avoid requiring a real seqrepo/translator setup
@pytest.fixture
def mock_build_variant_id():
    """Fixture to mock build_variant_id function."""
    with patch('adapters.BlueSTARR_variants_biosamples_adapter.build_variant_id') as mock_build:
        mock_build.return_value = 'NC_000010.11:100005302:A:C'
        yield mock_build


@patch('adapters.BlueSTARR_variants_biosamples_adapter.bulk_check_variants_in_arangodb', return_value=set())
def test_process_file_variant(mock_bulk_check, mock_file_fileset, mock_load_variant):
    writer = SpyWriter()
    adapter = BlueSTARRVariantBiosample(
        filepath=FILEPATH, writer=writer, label='variant', validate=True)

    with patch('builtins.open', mock_open(read_data=mock_bed_data)):
        adapter.process_file()

    first_item = json.loads(writer.contents[0])
    assert len(writer.contents) > 0
    assert first_item['_key'] == 'NC_000010.11:100005302:A:C'
    assert first_item['spdi'] == 'NC_000010.11:100005302:A:C'
    assert first_item['source'] == 'IGVF'
    assert first_item[
        'source_url'] == f'https://data.igvf.org/tabular-files/{FILE_ACCESSION}/'
    assert first_item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


@patch('adapters.BlueSTARR_variants_biosamples_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000010.11:100005302:A:C'})
def test_process_file_variant_biosample(mock_bulk_check, mock_file_fileset, mock_build_variant_id):
    # regression test: process_edge_chunk used to call self.biosample_term.replaceAll(...),
    # which doesn't exist on Python str (that's the JS method) and raised AttributeError on
    # the very first edge, so no BlueSTARR variant-biosample edges were ever written.
    writer = SpyWriter()
    adapter = BlueSTARRVariantBiosample(
        filepath=FILEPATH, writer=writer, label='variant_biosample', validate=True)

    with patch('builtins.open', mock_open(read_data=mock_bed_data)):
        adapter.process_file()

    assert len(writer.contents) > 0
    first_item = json.loads(writer.contents[0])
    # biosample_term's '/' must be replaced with '_' in the edge key
    assert first_item[
        '_key'] == f'NC_000010.11:100005302:A:C_ontology_terms_EFO_0002067_{FILE_ACCESSION}'
    assert first_item['_from'] == 'variants/NC_000010.11:100005302:A:C'
    assert first_item['_to'] == 'ontology_terms/EFO_0002067'
    assert first_item['genomic_element'] is None
    assert first_item['log2FC'] == 0.126
    assert first_item['class'] == 'prediction'
    assert first_item['label'] == 'predicted variant effect on gene expression'
    assert first_item['method'] == 'BlueSTARR'
    assert first_item['biological_context'] == 'K562'
    assert first_item['biosample_term'] == 'ontology_terms/EFO_0002067'
    assert first_item['name'] == 'modulates regulatory activity of'
    assert first_item['inverse_name'] == 'regulatory activity modulated by'
    assert first_item['source'] == 'IGVF'
    assert first_item[
        'source_url'] == f'https://data.igvf.org/tabular-files/{FILE_ACCESSION}/'
    assert first_item['files_filesets'] == f'files_filesets/{FILE_ACCESSION}'


def test_invalid_label(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: variant, variant_biosample'):
        BlueSTARRVariantBiosample(
            filepath=FILEPATH, label='invalid_label', writer=writer, validate=True)


def test_validate_doc_invalid(mock_file_fileset):
    writer = SpyWriter()
    adapter = BlueSTARRVariantBiosample(
        filepath=FILEPATH, label='variant_biosample', writer=writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
