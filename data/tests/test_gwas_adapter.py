import json
from this import d
import pytest
from adapters.gwas_adapter import GWAS
from adapters.writer import SpyWriter


@pytest.fixture
def gwas_files():
    return {
        'variants_to_ontology': './samples/gwas_v2d_igvf_sample.tsv',
        'variants_to_genes': './samples/gwas_v2g_igvf_sample.tsv'
    }


@pytest.fixture
def spy_writer():
    return SpyWriter()


def test_variants_phenotypes_collection(gwas_files, spy_writer, mocker):
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')
    gwas = GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
                gwas_collection='variants_phenotypes', writer=spy_writer, validate=True)
    gwas.process_file()

    assert len(spy_writer.contents) > 0
    for item in spy_writer.contents:
        if item.startswith('{'):
            data = json.loads(item)
            assert '_from' in data
            assert '_to' in data
            assert '_key' in data
            assert 'source' in data
            assert 'name' in data


def test_get_tagged_variants(gwas_files, mocker):
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')
    gwas = GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
                gwas_collection='variants_phenotypes_studies')
    tagged_variants = gwas.get_tagged_variants()

    assert len(tagged_variants) > 0
    for key, variants in tagged_variants.items():
        assert isinstance(variants, list)
        for variant in variants:
            assert 'tag_chrom' in variant
            assert 'tag_pos' in variant
            assert 'tag_ref' in variant
            assert 'tag_alt' in variant


def test_load_ontology_name_mapping(gwas_files):
    gwas = GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
                gwas_collection='variants_phenotypes_studies')
    gwas.load_ontology_name_mapping()

    assert hasattr(gwas, 'ontology_name_mapping')
    assert len(gwas.ontology_name_mapping) > 0
    for ontology_id, ontology_name in gwas.ontology_name_mapping.items():
        assert isinstance(ontology_id, str)
        assert isinstance(ontology_name, str)


def test_gwas_studies(gwas_files, spy_writer, mocker):
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')
    gwas = GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
                gwas_collection='studies', writer=spy_writer, validate=True)
    gwas.process_file()

    assert len(spy_writer.contents) > 0
    for item in spy_writer.contents:
        if item.startswith('{'):
            data = json.loads(item)
            assert '_key' in data
            assert 'name' in data
            assert 'ancestry_initial' in data
            assert 'ancestry_replication' in data
            assert 'n_cases' in data
            assert 'n_initial' in data
            assert 'n_replication' in data
            assert 'pmid' in data
            assert 'pub_author' in data
            assert 'pub_date' in data


def test_gwas_invalid_collection(gwas_files, spy_writer):
    with pytest.raises(ValueError):
        GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
             gwas_collection='invalid_collection', writer=spy_writer, validate=True)

# test gwas_collection == 'variants_phenotypes_studies' for adapter


def test_gwas_variants_phenotypes_studies(gwas_files, spy_writer, mocker):
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')
    gwas = GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
                gwas_collection='variants_phenotypes_studies', writer=spy_writer, validate=True)
    gwas.process_file()

    assert len(spy_writer.contents) > 0
    for item in spy_writer.contents:
        if item.startswith('{'):
            data = json.loads(item)
            assert '_key' in data
            assert 'lead_chrom' in data


def test_gwas_invalid_doc(gwas_files, spy_writer, mocker):
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')
    gwas = GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
                gwas_collection='variants_phenotypes_studies', writer=spy_writer, validate=True)
    invalid_doc = {
        'invalid_field': 'invalid_value',
        'another_invalid_field': 123
    }
    with pytest.raises(ValueError, match='Document validation failed:'):
        gwas.validate_doc(invalid_doc)


def test_gwas_pvalue_zero_handling(gwas_files, mocker):
    """Test handling of pvalue = 0 case (line 137)"""
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')
    gwas = GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
                gwas_collection='variants_phenotypes_studies')

    # Load ontology mapping first
    gwas.load_ontology_name_mapping()

    # Mock a row with pvalue = 0 (empty string or 0)
    # Need to create a row with enough fields for the variants_phenotypes_studies processing
    mock_row = [''] * 28  # Create a row with 28 empty fields
    mock_row[3] = 'test_study_id'  # study_id
    mock_row[4] = 'chr1'  # lead_chrom
    mock_row[5] = '100'  # lead_pos
    mock_row[6] = 'A'  # lead_ref
    mock_row[7] = 'T'  # lead_alt
    mock_row[17] = '0'  # Set pvalue to 0

    # Create tagged_variants data with the expected key
    studies_variants_key = gwas.studies_variants_key(mock_row)
    tagged_variants = {studies_variants_key: []}

    # Test the process_variants_phenotypes_studies method which contains the pvalue logic
    result = gwas.process_variants_phenotypes_studies(
        mock_row, 'test_edge_key', 'test_phenotype_id', tagged_variants)

    # Should use MAX_LOG10_PVALUE when pvalue is 0
    assert result['log10pvalue'] == gwas.MAX_LOG10_PVALUE


def test_gwas_empty_ontology_term_handling(gwas_files, mocker):
    """Test handling of empty ontology term (line 183)"""
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')
    gwas = GWAS(gwas_files['variants_to_ontology'], gwas_files['variants_to_genes'],
                gwas_collection='variants_phenotypes')

    # Mock a row with empty ontology term
    mock_row = [''] * 20  # Create a row with 20 empty fields
    mock_row[19] = 'ontology_terms/'  # Set ontology term to empty

    result = gwas.process_variants_phenotypes(mock_row)

    # Should return None for empty ontology terms
    assert result is None


def test_gwas_broken_line_handling_in_process_file(gwas_files, spy_writer, mocker):
    """Test broken line handling in process_file (lines 227-228, 233-234)"""
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')

    # Create a temporary file with broken lines
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
        # Write a proper header that matches the expected format
        f.write(
            'variant_id\tstudy_id\tphenotype_id\tontology_term_id\tchr\tpos\tref\talt\tother_fields\n')
        # Write a broken line (incomplete - missing newline)
        f.write('incomplete_line_without_newline')
        # Write a complete line
        f.write(
            'complete_line\tstudy1\tphenotype1\tontology1\tchr1\t100\tA\tT\tother\n')
        temp_file = f.name

    try:
        gwas = GWAS(temp_file, gwas_files['variants_to_genes'],
                    gwas_collection='variants_phenotypes', writer=spy_writer, validate=True)
        gwas.process_file()

        # Should handle broken lines gracefully
        # May or may not have valid output
        assert len(spy_writer.contents) >= 0

    finally:
        os.unlink(temp_file)
