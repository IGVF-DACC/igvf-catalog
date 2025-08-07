import json
import pytest
from adapters.igvf_MPRA_adapter import IGVFMPRAAdapter
from adapters.writer import SpyWriter
from unittest.mock import patch


@pytest.fixture
def mock_props():
    return {
        'simple_sample_summaries': ['K562'],
        'samples': ['ontology_terms/EFO_0002067'],
        'treatments_term_ids': [],
        'method': 'MPRA'
    }


@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf')
@patch('adapters.igvf_MPRA_adapter.bulk_check_variants_in_arangodb', return_value=set())
@patch('adapters.igvf_MPRA_adapter.load_variant')
def test_variant(mock_load_variant, mock_check, mock_query, mock_props):
    mock_query.return_value = (mock_props, None, None)
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
        writer=writer
    )
    adapter.process_file()
    assert any(
        '"spdi": "NC_000009.12:135961939:C:T"' in entry for entry in writer.contents)


@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf')
def test_genomic_element(mock_query, mock_props):
    mock_query.return_value = (mock_props, None, None)

    writer = SpyWriter()
    adapter = IGVFMPRAAdapter(
        filepath='./samples/igvf_mpra_element_effects.example.tsv',
        label='genomic_element',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
        writer=writer
    )
    adapter.process_file()
    parsed = [json.loads(x) for x in writer.contents]
    assert any(p['chr'] == 'chr9' and p['type'] ==
               'tested elements' for p in parsed)


@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf')
def test_elements_from_variant_file(mock_query, mock_props):
    mock_query.side_effect = [
        (mock_props, None, None),
        (mock_props, None, None),
    ]

    writer = SpyWriter()
    adapter = IGVFMPRAAdapter(
        filepath='./samples/igvf_mpra_variant_effects.example.tsv',
        label='genomic_element_from_variant',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
        writer=writer
    )
    adapter.process_file()
    parsed = [json.loads(x) for x in writer.contents]
    assert any(p['chr'] == 'chr9' and p['type'] ==
               'tested elements' for p in parsed)


@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf')
@patch('adapters.igvf_MPRA_adapter.bulk_check_variants_in_arangodb', return_value={'NC_000009.12:136248440:T:C'})
@patch('adapters.igvf_MPRA_adapter.load_variant')
def test_variant_genomic_element(mock_load_variant, mock_check, mock_query, mock_props):
    mock_query.side_effect = [
        (mock_props, None, None),  # for data file
        (mock_props, None, None),  # for reference file
    ]

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
        writer=writer
    )

    adapter.process_file()

    parsed = [json.loads(x) for x in writer.contents]
    assert any(
        p['_from'] == 'variants/NC_000009.12:136248440:T:C' and
        p['_to'] == 'genomic_elements/MPRA_chr9_97238011_97238211_GRCh38_IGVFFI4914OUJH'
        for p in parsed
    )


@patch('adapters.file_fileset_adapter.FileFileSet.query_fileset_files_props_igvf')
def test_genomic_element_biosample(mock_query, mock_props):
    mock_query.return_value = (mock_props, None, None)

    writer = SpyWriter()
    adapter = IGVFMPRAAdapter(
        filepath='./samples/igvf_mpra_element_effects.example.tsv',
        label='genomic_element_biosample',
        source_url='https://api.data.igvf.org/tabular-files/IGVFFI1323RCIE/',
        reference_filepath='./samples/igvf_mpra_sequence_designs.example.tsv',
        reference_source_url='https://api.data.igvf.org/tabular-files/IGVFFI4914OUJH/',
        writer=writer
    )
    adapter.process_file()
    parsed = [json.loads(x) for x in writer.contents]
    assert all(p['_from'].startswith('genomic_elements/')
               and p['_to'].startswith('ontology_terms/') for p in parsed)
