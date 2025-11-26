import json
import pytest
from adapters.igvf_MPRA_adapter import IGVFMPRAAdapter
from adapters.writer import SpyWriter
from unittest.mock import patch


# mock get_file_fileset_by_accession_in_arangodb so files_fileset data change will not affect the test
@pytest.fixture
def mock_file_fileset():
    """Fixture to mock get_file_fileset_by_accession_in_arangodb function."""
    with patch('adapters.igvf_MPRA_adapter.get_file_fileset_by_accession_in_arangodb') as mock_get_file_fileset:
        # Default return value for main file (used in __init__)
        default_fileset = {
            'method': 'lentiMPRA',
            'class': 'observed data',
            'samples': ['ontology_terms/CL_0000679'],
            'simple_sample_summaries': [
                'glutamatergic neuron differentiated cell specimen, pooled cell'

            ],
            'treatments_term_ids': None
        }
        # Return value for reference file (used in process_file for process_genomic_element_chunk)
        reference_fileset = {
            'method': 'GRCh38 elements',
            'class': 'observed data',
            'samples': ['ontology_terms/EFO_0002067'],
            'simple_sample_summaries': ['K562'],
            'treatments_term_ids': []
        }
        # Use side_effect to return different values based on call order
        # First call (in __init__ for file_accession) returns default_fileset
        # Second call (in process_file for reference_file_accession) returns reference_fileset
        # For tests that only create adapter without calling process_file, only first value is used
        mock_get_file_fileset.side_effect = [
            default_fileset, reference_fileset]
        yield mock_get_file_fileset


@patch('adapters.igvf_MPRA_adapter.bulk_check_variants_in_arangodb', return_value=set())
@patch('adapters.igvf_MPRA_adapter.load_variant')
def test_variant(mock_load_variant, mock_check, mock_file_fileset):
    mock_load_variant.return_value = ({
        '_key': 'NC_000009.12:135961939:C:T',
        'spdi': 'NC_000009.12:135961939:C:T',
        'hgvs': 'NC_000009.12:g.135961940C>T',
        'variation_type': 'SNP',
    }, None)

    writer = SpyWriter()
    adapter = IGVFMPRAAdapter(
        filepath='./samples/igvf_mpra_variant_effects.example.tsv',
        label='variant',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    assert any(
        '"spdi": "NC_000009.12:135961939:C:T"' in entry for entry in writer.contents)


def test_genomic_element(mock_file_fileset):

    writer = SpyWriter()
    adapter = IGVFMPRAAdapter(
        filepath='./samples/igvf_mpra_element_effects.example.tsv',
        label='genomic_element',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    parsed = [json.loads(x) for x in writer.contents]
    assert any(p['chr'] == 'chr9' and p['type'] ==
               'tested elements' and p['method'] == 'GRCh38 elements' for p in parsed)


def test_elements_from_variant_file(mock_file_fileset):

    writer = SpyWriter()
    adapter = IGVFMPRAAdapter(
        filepath='./samples/igvf_mpra_variant_effects.example.tsv',
        label='genomic_element_from_variant',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    parsed = [json.loads(x) for x in writer.contents]
    assert any(p['chr'] == 'chr9' and p['type'] ==
               'tested elements' for p in parsed)


@patch('adapters.igvf_MPRA_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000009.12:136248440:T:C'})
@patch('adapters.igvf_MPRA_adapter.load_variant')
def test_variant_genomic_element(mock_load_variant, mock_check, mock_file_fileset):

    mock_load_variant.return_value = ({
        '_key': 'NC_000009.12:136248440:T:C',
    }, None)

    writer = SpyWriter()
    adapter = IGVFMPRAAdapter(
        filepath='./samples/igvf_mpra_variant_effects.example.tsv',
        label='variant_genomic_element',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
        writer=writer,
        validate=True
    )

    adapter.process_file()

    # Parse all items and find the expected one by _key (order may vary due to set iteration)
    parsed_items = [json.loads(item) for item in writer.contents]
    expected_key = 'NC_000009.12:136248440:T:C_MPRA_chr9_136886228_136886428_GRCh38_IGVFFI4914OUJH_IGVFFI1323RCIE'
    found_item = next(
        (item for item in parsed_items if item['_key'] == expected_key), None)

    assert found_item is not None, f"Expected item with _key '{expected_key}' not found in writer contents"
    assert found_item == {
        '_key': 'NC_000009.12:136248440:T:C_MPRA_chr9_136886228_136886428_GRCh38_IGVFFI4914OUJH_IGVFFI1323RCIE',
        '_from': 'variants/NC_000009.12:136248440:T:C',
        '_to': 'genomic_elements/MPRA_chr9_136886228_136886428_GRCh38_IGVFFI4914OUJH',
        'bed_score': 66,
        'activity_score': -0.0768,
        'DNA_count_ref': 0.5948,
        'RNA_count_ref': 0.3434,
        'DNA_count_alt': 0.6516,
        'RNA_count_alt': 0.3039,
        'minusLog10PValue': 5.9634,
        'minusLog10QValue': 4.7221,
        'postProbEffect': 0.992,
        'CI_lower_95': -0.1076,
        'CI_upper_95': -0.0461,
        'class': 'observed data',
        'label': 'variant effect on regulatory element activity',
        'biological_context': 'glutamatergic neuron differentiated cell specimen, pooled cell',
        'biosample_term': 'ontology_terms/CL_0000679',
        'treatments_term_ids': None,
        'name': 'modulates regulatory activity of',
        'inverse_name': 'regulatory activity modulated by',
        'method': 'lentiMPRA',
        'source': 'IGVF',
        'source_url': 'https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        'files_filesets': 'files_filesets/IGVFFI1323RCIE',
    }


def test_genomic_element_biosample(mock_file_fileset):

    writer = SpyWriter()
    adapter = IGVFMPRAAdapter(
        filepath='./samples/igvf_mpra_element_effects.example.tsv',
        label='genomic_element_biosample',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
        writer=writer,
        validate=True
    )
    adapter.process_file()
    parsed = [json.loads(x) for x in writer.contents]
    assert all(p['_from'].startswith('genomic_elements/')
               and p['_to'].startswith('ontology_terms/') for p in parsed)


def test_invalid_label(mock_file_fileset):
    writer = SpyWriter()
    with pytest.raises(ValueError, match='Invalid label: invalid_label. Allowed values: genomic_element, genomic_element_biosample, variant, genomic_element_from_variant, variant_genomic_element'):
        IGVFMPRAAdapter(
            filepath='./samples/igvf_mpra_element_effects.example.tsv',
            label='invalid_label',
            source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
            reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
            reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
            writer=writer,
            validate=True)


def test_validate_doc_invalid(mock_file_fileset):
    writer = SpyWriter()
    adapter = IGVFMPRAAdapter(
        filepath='./samples/igvf_mpra_element_effects.example.tsv',
        label='genomic_element',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
        writer=writer,
        validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        adapter.validate_doc(invalid_doc)
