"""Tests for ID parser."""

import pytest
from igvf_catalog_mcp.services.id_parser import IDParser


class TestIDParser:
    """Test ID parser functionality."""

    def test_detect_gene_ensembl(self):
        """Test detection of Ensembl gene IDs."""
        entity_type, param_name = IDParser.detect_entity_type(
            'ENSG00000139618')
        assert entity_type == 'gene'
        assert param_name == 'gene_id'

    def test_detect_gene_symbol(self):
        """Test detection of gene symbols."""
        entity_type, param_name = IDParser.detect_entity_type('BRCA1')
        assert entity_type == 'gene'
        assert param_name == 'gene_name'

    def test_detect_gene_hgnc(self):
        """Test detection of HGNC IDs."""
        entity_type, param_name = IDParser.detect_entity_type('HGNC:1100')
        assert entity_type == 'gene'
        assert param_name == 'hgnc_id'

    def test_detect_variant_rsid(self):
        """Test detection of rsID variants."""
        entity_type, param_name = IDParser.detect_entity_type('rs12345')
        assert entity_type == 'variant'
        assert param_name == 'rsid'

    def test_detect_variant_spdi(self):
        """Test detection of SPDI format variants."""
        entity_type, param_name = IDParser.detect_entity_type(
            'NC_000001.11:12345:A:G')
        assert entity_type == 'variant'
        assert param_name == 'spdi'

    def test_detect_variant_hgvs(self):
        """Test detection of HGVS format variants."""
        entity_type, param_name = IDParser.detect_entity_type(
            'NC_000001.11:g.12346A>G')
        assert entity_type == 'variant'
        assert param_name == 'hgvs'

    def test_detect_variant_ca_id(self):
        """Test detection of ClinGen Allele IDs."""
        entity_type, param_name = IDParser.detect_entity_type('CA12345')
        assert entity_type == 'variant'
        assert param_name == 'ca_id'

    def test_detect_protein_ensembl(self):
        """Test detection of Ensembl protein IDs."""
        entity_type, param_name = IDParser.detect_entity_type(
            'ENSP00000493376')
        assert entity_type == 'protein'
        assert param_name == 'protein_id'

    def test_detect_protein_uniprot(self):
        """Test detection of UniProt IDs."""
        entity_type, param_name = IDParser.detect_entity_type('P49711')
        assert entity_type == 'protein'
        assert param_name == 'protein_id'

    def test_detect_transcript(self):
        """Test detection of transcript IDs."""
        entity_type, param_name = IDParser.detect_entity_type(
            'ENST00000443707')
        assert entity_type == 'transcript'
        assert param_name == 'transcript_id'

    def test_detect_ontology_orphanet(self):
        """Test detection of Orphanet IDs."""
        entity_type, param_name = IDParser.detect_entity_type('Orphanet_586')
        assert entity_type == 'ontology'
        assert param_name == 'term_id'

    def test_detect_ontology_mondo(self):
        """Test detection of MONDO IDs."""
        entity_type, param_name = IDParser.detect_entity_type('MONDO_0008199')
        assert entity_type == 'ontology'
        assert param_name == 'term_id'

    def test_detect_drug(self):
        """Test detection of drug IDs."""
        entity_type, param_name = IDParser.detect_entity_type('PA448497')
        assert entity_type == 'drug'
        assert param_name == 'drug_id'

    def test_detect_complex(self):
        """Test detection of complex IDs."""
        entity_type, param_name = IDParser.detect_entity_type('CPX-9')
        assert entity_type == 'complex'
        assert param_name == 'complex_id'

    def test_detect_pathway(self):
        """Test detection of pathway IDs."""
        entity_type, param_name = IDParser.detect_entity_type('R-HSA-164843')
        assert entity_type == 'pathway'
        assert param_name == 'pathway_id'

    def test_detect_with_hint(self):
        """Test detection with hint parameter."""
        # Gene symbol could be ambiguous, but hint helps
        entity_type, param_name = IDParser.detect_entity_type(
            'TP53', hint='gene')
        assert entity_type == 'gene'
        assert param_name == 'gene_name'

    def test_invalid_identifier(self):
        """Test that invalid identifiers raise ValueError."""
        with pytest.raises(ValueError, match='Could not detect entity type'):
            IDParser.detect_entity_type('invalid_id_12345!@#')

    def test_normalize_gene_symbol(self):
        """Test normalization of gene symbols to uppercase."""
        normalized = IDParser.normalize_identifier('brca1', 'gene')
        assert normalized == 'BRCA1'

    def test_normalize_ontology_separator(self):
        """Test normalization of ontology term separators."""
        normalized = IDParser.normalize_identifier('MONDO:0008199', 'ontology')
        assert normalized == 'MONDO_0008199'

    def test_get_api_endpoint(self):
        """Test API endpoint retrieval."""
        assert IDParser.get_api_endpoint('gene') == '/api/genes'
        assert IDParser.get_api_endpoint('variant') == '/api/variants'
        assert IDParser.get_api_endpoint('protein') == '/api/proteins'
