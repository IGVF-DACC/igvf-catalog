"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_gene_data():
    """Sample gene data for testing."""
    return {
        '_id': 'ENSG00000139618',
        'name': 'BRCA2',
        'chr': 'chr13',
        'start': 32315474,
        'end': 32400266,
        'gene_type': 'protein_coding',
        'hgnc': 'HGNC:1101',
        'entrez': 'ENTREZ:675',
        'synonyms': ['FANCD1', 'BRCC2'],
        'organism': 'Homo sapiens',
    }


@pytest.fixture
def sample_variant_data():
    """Sample variant data for testing."""
    return {
        '_id': 'NC_000017.11:43044295:G:A',
        'chr': 'chr17',
        'pos': 43044295,
        'ref': 'G',
        'alt': 'A',
        'rsid': ['rs80357906'],
        'spdi': 'NC_000017.11:43044295:G:A',
        'hgvs': 'NC_000017.11:g.43044296G>A',
        'ca_id': 'CA6028682',
        'annotations': {
            'gnomad_af_total': 0.00001,
            'cadd_phred': 25.3,
            'GENCODE_category': 'coding',
        },
    }


@pytest.fixture
def sample_region():
    """Sample genomic region for testing."""
    return {
        'chromosome': 'chr17',
        'start': 41000000,
        'end': 42000000,
    }
