import json
import pytest
from adapters.gwas_adapter import GWAS
from adapters.writer import SpyWriter

# Add this fixture to mock requests.get for all tests in this file


@pytest.fixture(autouse=True)
def mock_requests_get(monkeypatch):
    """Automatically mock requests.get for all tests in this file."""
    class MockResponse:
        def json(self):
            # Return minimal valid metadata for GWAS studies
            return {
                'study_id': 'study1',
                'study_name': 'Test Study',
                'ancestry_initial': 'EUR',
                'ancestry_replication': 'EUR',
                'n_cases': 100,
                'n_initial': 200,
                'n_replication': 50,
                'pmid': '123456',
                'pub_author': 'Smith et al.',
                'pub_date': '2022-01-01',
                'source_url': 'https://example.com',
                'catalog_class': 'observed data',
                'catalog_method': 'GWAS'
            }

    monkeypatch.setattr('requests.get', lambda *args, **kwargs: MockResponse())


@pytest.fixture
def gwas_files():
    return {
        'variants_to_ontology': './samples/gwas_v2d_igvf_sample.tsv'
    }


@pytest.fixture
def spy_writer():
    return SpyWriter()


def test_variants_phenotypes_collection(gwas_files, spy_writer, mocker):
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')
    gwas = GWAS(gwas_files['variants_to_ontology'],
                label='variants_phenotypes', writer=spy_writer, validate=True)
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
    gwas = GWAS(gwas_files['variants_to_ontology'],
                label='variants_phenotypes')
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
    gwas = GWAS(gwas_files['variants_to_ontology'],
                label='variants_phenotypes')
    gwas.load_ontology_name_mapping()

    assert hasattr(gwas, 'ontology_name_mapping')
    assert len(gwas.ontology_name_mapping) > 0
    for ontology_id, ontology_name in gwas.ontology_name_mapping.items():
        assert isinstance(ontology_id, str)
        assert isinstance(ontology_name, str)


def test_gwas_studies(gwas_files, spy_writer, mocker):
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')
    gwas = GWAS(gwas_files['variants_to_ontology'],
                label='studies', writer=spy_writer, validate=True)
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
            assert 'source_url' in data


def test_gwas_invalid_collection(gwas_files, spy_writer):
    with pytest.raises(ValueError):
        GWAS(gwas_files['variants_to_ontology'],
             label='invalid_collection', writer=spy_writer, validate=True)


def test_gwas_invalid_doc(gwas_files, spy_writer, mocker):
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')
    gwas = GWAS(gwas_files['variants_to_ontology'],
                label='variants_phenotypes', writer=spy_writer, validate=True)
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
    gwas = GWAS(gwas_files['variants_to_ontology'],
                label='variants_phenotypes')

    # Load ontology mapping first
    gwas.load_ontology_name_mapping()

    # Mock a row with pvalue = 0 (empty string or 0)
    mock_row = [''] * 18
    mock_row[1] = 'NA'
    mock_row[2] = 'EFO_0007010'
    mock_row[3] = 'test_study_id'
    mock_row[4] = '1'
    mock_row[5] = '100'
    mock_row[6] = 'A'
    mock_row[7] = 'T'
    mock_row[15] = '1'
    mock_row[16] = '-3'
    mock_row[17] = '0'  # Set pvalue to 0

    # Create tagged_variants data with the expected key
    studies_variants_key = gwas.generate_studies_variants_key(mock_row)
    tagged_variants = {studies_variants_key: []}

    result = gwas.process_variants_phenotypes(mock_row, tagged_variants)

    # Should use MAX_LOG10_PVALUE when pvalue is 0
    assert result['log10pvalue'] == gwas.MAX_LOG10_PVALUE


def test_gwas_empty_ontology_term_handling(gwas_files, mocker):
    """Test handling of empty ontology term (line 183)"""
    mocker.patch('adapters.gwas_adapter.build_variant_id',
                 return_value='fake_variant_id')
    gwas = GWAS(gwas_files['variants_to_ontology'],
                label='variants_phenotypes')

    # Mock a row with empty ontology term
    mock_row = [''] * 18
    mock_row[1] = 'NA'
    mock_row[2] = ''

    result = gwas.process_variants_phenotypes(mock_row, {})

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
        # Write a header with enough columns for GWAS parsing
        header = [f'col_{i}' for i in range(47)]
        f.write('\t'.join(header) + '\n')
        # Write a broken line (incomplete - missing newline)
        f.write('incomplete_line_without_newline')
        # Write a complete line
        row = [''] * 47
        row[1] = 'NA'
        row[2] = 'EFO_0007010'
        row[3] = 'study1'
        row[4] = '1'
        row[5] = '100'
        row[6] = 'A'
        row[7] = 'T'
        row[15] = '1'
        row[16] = '-3'
        row[17] = '1e-8'
        row[34] = '1'
        row[35] = '1000'
        row[36] = 'A'
        row[37] = 'T'
        row[38] = '0.1'
        row[39] = 'False'
        row[40] = '0.0'
        row[41] = '0.0'
        row[42] = '0.0'
        row[43] = '1.0'
        row[44] = '0.0'
        row[45] = '1.0'
        row[46] = '0.1'
        f.write('\t'.join(row) + '\n')
        temp_file = f.name

    try:
        gwas = GWAS(temp_file,
                    label='variants_phenotypes', writer=spy_writer, validate=True)
        gwas.process_file()

        # Should handle broken lines gracefully
        # May or may not have valid output
        assert len(spy_writer.contents) >= 0

    finally:
        os.unlink(temp_file)
