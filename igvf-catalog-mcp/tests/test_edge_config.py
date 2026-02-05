"""Tests for edge configuration system."""

import pytest

from igvf_catalog_mcp.services.edge_config import (
    EDGE_ENDPOINTS,
    RELATIONSHIP_TYPE_MAPPING,
    get_edge_config,
    get_endpoints_for_entity_and_relationship,
    get_all_sources,
    get_sources_by_category,
)


class TestEdgeEndpoints:
    """Test edge endpoint configuration."""

    def test_all_endpoints_have_required_fields(self):
        """Verify all endpoints have required configuration fields."""
        required_fields = ['path', 'from_type', 'max_limit']

        for endpoint_key, config in EDGE_ENDPOINTS.items():
            for field in required_fields:
                assert field in config, f'Endpoint {endpoint_key} missing field: {field}'

    def test_endpoint_paths_are_unique(self):
        """Verify all endpoint paths are unique."""
        paths = [config['path'] for config in EDGE_ENDPOINTS.values()]
        assert len(paths) == len(set(paths)), 'Duplicate endpoint paths found'

    def test_bidirectional_endpoints_exist(self):
        """Verify bidirectional endpoints are properly configured."""
        bidirectional_pairs = [
            ('variants_genes', 'genes_variants'),
            ('variants_proteins', 'proteins_variants'),
            ('variants_drugs', 'drugs_variants'),
            ('genes_diseases', 'diseases_genes'),
            ('genes_transcripts', 'transcripts_genes'),
            ('transcripts_proteins', 'proteins_transcripts'),
            ('complexes_proteins', 'proteins_complexes'),
            ('motifs_proteins', 'proteins_motifs'),
        ]

        for pair in bidirectional_pairs:
            assert pair[0] in EDGE_ENDPOINTS, f'Missing endpoint: {pair[0]}'
            assert pair[1] in EDGE_ENDPOINTS, f'Missing endpoint: {pair[1]}'

    def test_sources_are_lists(self):
        """Verify sources field contains lists of strings."""
        for endpoint_key, config in EDGE_ENDPOINTS.items():
            if 'sources' in config:
                assert isinstance(
                    config['sources'], list
                ), f'Endpoint {endpoint_key} sources should be a list'
                assert all(
                    isinstance(s, str) for s in config['sources']
                ), f'Endpoint {endpoint_key} sources should contain strings'

    def test_max_limits_are_reasonable(self):
        """Verify max_limit values are reasonable."""
        for endpoint_key, config in EDGE_ENDPOINTS.items():
            max_limit = config.get('max_limit', 100)
            assert 25 <= max_limit <= 1000, f'Endpoint {endpoint_key} has unreasonable max_limit: {max_limit}'


class TestGetEdgeConfig:
    """Test get_edge_config function."""

    def test_get_existing_endpoint(self):
        """Test retrieving configuration for an existing endpoint."""
        config = get_edge_config('variants_genes')
        assert config is not None
        assert config['path'] == '/api/variants/genes'
        assert config['from_type'] == 'variant'
        assert config['to_type'] == 'gene'

    def test_get_nonexistent_endpoint(self):
        """Test retrieving configuration for a non-existent endpoint."""
        config = get_edge_config('nonexistent_endpoint')
        assert config is None

    def test_variants_genes_has_correct_sources(self):
        """Test variants_genes endpoint has correct source values."""
        config = get_edge_config('variants_genes')
        assert 'AFGR' in config['sources']
        assert 'EBI eQTL Catalogue' in config['sources']
        assert 'IGVF' in config['sources']
        # Old incorrect value should not be present
        assert 'GTEx' not in config.get('sources', [])

    def test_variants_proteins_has_correct_sources(self):
        """Test variants_proteins endpoint has correct source values."""
        config = get_edge_config('variants_proteins')
        assert 'ADASTRA' in config['sources']
        assert 'GVATdb' in config['sources']
        assert 'UKB' in config['sources']
        assert 'SEMVAR' in config['sources']

    def test_variants_phenotypes_has_correct_methods(self):
        """Test variants_phenotypes endpoint has correct method values."""
        config = get_edge_config('variants_phenotypes')
        assert 'methods' in config
        assert 'cV2F' in config['methods']
        assert 'SGE' in config['methods']


class TestRelationshipTypeMapping:
    """Test relationship type mapping functionality."""

    def test_all_relationship_types_defined(self):
        """Verify all expected relationship types are defined."""
        expected_types = [
            'regulatory',
            'genetic',
            'physical',
            'functional',
            'pharmacological',
            'ld',
            'coding',
            'transcription',
        ]

        for rel_type in expected_types:
            assert (
                rel_type in RELATIONSHIP_TYPE_MAPPING
            ), f'Missing relationship type: {rel_type}'

    def test_get_endpoints_for_variant_regulatory(self):
        """Test getting regulatory endpoints for variants."""
        endpoints = get_endpoints_for_entity_and_relationship(
            'variant', 'regulatory')
        assert 'variants_genes' in endpoints
        assert 'variants_genomic_elements' in endpoints

    def test_get_endpoints_for_gene_regulatory(self):
        """Test getting regulatory endpoints for genes."""
        endpoints = get_endpoints_for_entity_and_relationship(
            'gene', 'regulatory')
        assert 'genes_variants' in endpoints
        assert 'genomic_elements_genes' in endpoints

    def test_get_endpoints_for_variant_ld(self):
        """Test getting LD endpoints for variants."""
        endpoints = get_endpoints_for_entity_and_relationship('variant', 'ld')
        assert 'variants_variants' in endpoints

    def test_get_endpoints_for_protein_physical(self):
        """Test getting physical interaction endpoints for proteins."""
        endpoints = get_endpoints_for_entity_and_relationship(
            'protein', 'physical')
        assert 'proteins_proteins' in endpoints
        assert 'proteins_complexes' in endpoints

    def test_get_endpoints_for_invalid_relationship(self):
        """Test getting endpoints for an invalid relationship type."""
        endpoints = get_endpoints_for_entity_and_relationship(
            'gene', 'invalid_relationship')
        assert endpoints == []

    def test_get_endpoints_for_invalid_entity_type(self):
        """Test getting endpoints when entity type doesn't match relationship."""
        endpoints = get_endpoints_for_entity_and_relationship('gene', 'ld')
        assert endpoints == []


class TestSourceManagement:
    """Test source management functions."""

    def test_get_all_sources_returns_unique_sources(self):
        """Test that get_all_sources returns unique source names."""
        sources = get_all_sources()
        assert isinstance(sources, set)
        assert len(sources) > 0

        # Check for known sources
        expected_sources = {'AFGR', 'EBI eQTL Catalogue',
                            'ADASTRA', 'GVATdb', 'PharmGKB', 'Orphanet'}
        for source in expected_sources:
            assert source in sources, f'Expected source {source} not found'

    def test_get_sources_by_category_structure(self):
        """Test that get_sources_by_category returns proper structure."""
        sources_by_cat = get_sources_by_category()
        assert isinstance(sources_by_cat, dict)

        expected_categories = [
            'variant_annotations',
            'gene_expression',
            'regulatory',
            'disease',
            'drugs',
            'interactions',
        ]

        for category in expected_categories:
            assert category in sources_by_cat, f'Missing category: {category}'
            assert isinstance(sources_by_cat[category], list)

    def test_gene_expression_category_sources(self):
        """Test gene expression category has correct sources."""
        sources_by_cat = get_sources_by_category()
        gene_exp_sources = sources_by_cat['gene_expression']

        assert 'AFGR' in gene_exp_sources
        assert 'EBI eQTL Catalogue' in gene_exp_sources
        assert 'IGVF' in gene_exp_sources

    def test_regulatory_category_sources(self):
        """Test regulatory category has correct sources."""
        sources_by_cat = get_sources_by_category()
        reg_sources = sources_by_cat['regulatory']

        assert 'ADASTRA' in reg_sources
        assert 'GVATdb' in reg_sources
        assert 'SEMVAR' in reg_sources


class TestFilterConfiguration:
    """Test filter configuration for endpoints."""

    def test_variants_genes_filters(self):
        """Test variants_genes endpoint has correct filter configuration."""
        config = get_edge_config('variants_genes')
        filters = config.get('filters', {})

        assert 'log10pvalue' in filters
        assert filters['log10pvalue'] == 'range'
        assert 'effect_size' in filters
        assert filters['effect_size'] == 'range'
        assert 'biological_context' in filters
        assert filters['biological_context'] == 'string'

    def test_variants_variants_ld_filters(self):
        """Test variants_variants endpoint has LD-specific filters."""
        config = get_edge_config('variants_variants')
        filters = config.get('filters', {})

        assert 'r2' in filters
        assert filters['r2'] == 'range'
        assert 'd_prime' in filters
        assert filters['d_prime'] == 'range'
        assert 'ancestry' in filters
        assert filters['ancestry'] == 'enum'

    def test_variants_drugs_filters(self):
        """Test variants_drugs endpoint has appropriate filters."""
        config = get_edge_config('variants_drugs')
        filters = config.get('filters', {})

        assert 'pmid' in filters
        assert 'phenotype_categories' in filters


class TestParameterConfiguration:
    """Test parameter configuration for endpoints."""

    def test_variants_genes_from_params(self):
        """Test variants_genes has correct from_params."""
        config = get_edge_config('variants_genes')
        from_params = config.get('from_params', [])

        assert 'variant_id' in from_params
        assert 'spdi' in from_params
        assert 'hgvs' in from_params
        assert 'rsid' in from_params
        assert 'ca_id' in from_params

    def test_genes_variants_from_params(self):
        """Test genes_variants has correct from_params."""
        config = get_edge_config('genes_variants')
        from_params = config.get('from_params', [])

        assert 'gene_id' in from_params
        assert 'gene_name' in from_params
        assert 'hgnc_id' in from_params
        assert 'alias' in from_params

    def test_proteins_variants_from_params(self):
        """Test proteins_variants has correct from_params."""
        config = get_edge_config('proteins_variants')
        from_params = config.get('from_params', [])

        assert 'protein_id' in from_params
        assert 'protein_name' in from_params
        assert 'full_name' in from_params
        assert 'dbxrefs' in from_params


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
