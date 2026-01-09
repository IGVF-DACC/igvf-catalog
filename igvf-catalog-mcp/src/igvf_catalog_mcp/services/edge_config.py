"""Edge endpoint configuration for the IGVF Catalog API.

This module defines the structure and parameters for all edge (relationship) endpoints
in the IGVF Catalog API. It provides a centralized configuration that tools can use
to build correct queries with proper parameter names, source values, and filters.
"""

from typing import Literal, TypedDict

EntityType = Literal[
    'gene',
    'transcript',
    'protein',
    'variant',
    'ontology',
    'drug',
    'complex',
    'study',
    'pathway',
    'genomic_element',
    'coding_variant',
]


class EdgeEndpointConfig(TypedDict, total=False):
    """Configuration for an edge endpoint."""

    path: str
    from_type: EntityType
    to_type: EntityType
    from_params: list[str]  # Valid parameter names for the "from" entity
    # Valid parameter names for the "to" entity (if bidirectional)
    to_params: list[str]
    sources: list[str]  # Valid source values
    labels: list[str]  # Valid label/edge type values
    methods: list[str]  # Valid method values
    filters: dict[str, str]  # Filter name -> type (range, string, enum)
    supports_verbose: bool  # Whether the endpoint supports verbose mode
    max_limit: int  # Maximum page size


# Complete edge endpoint registry
EDGE_ENDPOINTS: dict[str, EdgeEndpointConfig] = {
    # Variant-Gene relationships (eQTLs, sQTLs)
    'variants_genes': {
        'path': '/api/variants/genes',
        'from_type': 'variant',
        'to_type': 'gene',
        'from_params': ['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id'],
        'sources': ['AFGR', 'EBI eQTL Catalogue', 'IGVF'],
        'labels': ['eQTL', 'splice_QTL', 'variant effect on gene expression'],
        'methods': ['Variant-EFFECTS'],
        'filters': {
            'log10pvalue': 'range',
            'effect_size': 'range',
            'biological_context': 'string',
            'files_fileset': 'string',
        },
        'supports_verbose': True,
        'max_limit': 500,
    },
    'genes_variants': {
        'path': '/api/genes/variants',
        'from_type': 'gene',
        'to_type': 'variant',
        'from_params': ['gene_id', 'gene_name', 'hgnc_id', 'alias'],
        'sources': ['AFGR', 'EBI eQTL Catalogue', 'IGVF'],
        'labels': ['eQTL', 'splice_QTL', 'variant effect on gene expression'],
        'methods': ['Variant-EFFECTS'],
        'filters': {
            'log10pvalue': 'range',
            'effect_size': 'range',
            'biological_context': 'string',
            'files_fileset': 'string',
        },
        'supports_verbose': True,
        'max_limit': 500,
    },
    # Variant-Protein relationships (pQTL, allele-specific binding)
    'variants_proteins': {
        'path': '/api/variants/proteins',
        'from_type': 'variant',
        'to_type': 'protein',
        'from_params': ['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id', 'region'],
        'sources': ['ADASTRA', 'GVATdb', 'UKB', 'SEMVAR'],
        'labels': ['pQTL', 'allele-specific binding'],
        'methods': ['SEMVAR'],
        'filters': {
            'files_fileset': 'string',
            'log10pvalue': 'range',
        },
        'supports_verbose': True,
        'max_limit': 100,
    },
    'proteins_variants': {
        'path': '/api/proteins/variants',
        'from_type': 'protein',
        'to_type': 'variant',
        'from_params': ['protein_id', 'protein_name', 'full_name', 'dbxrefs'],
        'sources': ['ADASTRA', 'GVATdb', 'UKB', 'SEMVAR'],
        'labels': ['pQTL', 'allele-specific binding'],
        'methods': ['SEMVAR'],
        'filters': {},
        'supports_verbose': True,
        'max_limit': 100,
    },
    # Variant-Phenotype relationships (GWAS)
    'variants_phenotypes': {
        'path': '/api/variants/phenotypes',
        'from_type': 'variant',
        'to_type': 'ontology',
        'from_params': ['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id', 'region'],
        'sources': ['OpenTargets', 'IGVF'],
        'methods': ['cV2F', 'SGE'],
        'filters': {
            'log10pvalue': 'range',
            'phenotype_id': 'string',
            'files_fileset': 'string',
        },
        'supports_verbose': True,
        'max_limit': 100,
    },
    'phenotypes_variants': {
        'path': '/api/phenotypes/variants',
        'from_type': 'ontology',
        'to_type': 'variant',
        'from_params': ['phenotype_id', 'phenotype_name'],
        'sources': ['OpenTargets', 'IGVF'],
        'methods': ['cV2F', 'SGE'],
        'filters': {
            'log10pvalue': 'range',
            'files_fileset': 'string',
        },
        'supports_verbose': True,
        'max_limit': 100,
    },
    # Variant-Drug relationships (PharmGKB)
    'variants_drugs': {
        'path': '/api/variants/drugs',
        'from_type': 'variant',
        'to_type': 'drug',
        'from_params': ['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id'],
        'sources': ['PharmGKB'],
        'filters': {
            'pmid': 'string',
            'phenotype_categories': 'string',
            'GENCODE_category': 'enum',
        },
        'supports_verbose': True,
        'max_limit': 100,
    },
    'drugs_variants': {
        'path': '/api/drugs/variants',
        'from_type': 'drug',
        'to_type': 'variant',
        'from_params': ['drug_id', 'drug_name'],
        'sources': ['PharmGKB'],
        'filters': {
            'pmid': 'string',
            'phenotype_categories': 'string',
        },
        'supports_verbose': True,
        'max_limit': 100,
    },
    # Variant-Disease relationships (ClinGen)
    'variants_diseases': {
        'path': '/api/variants/diseases',
        'from_type': 'variant',
        'to_type': 'ontology',
        'from_params': ['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id'],
        'sources': ['ClinGen'],
        'filters': {
            'disease_name': 'string',
            'disease_id': 'string',
        },
        'supports_verbose': True,
        'max_limit': 100,
    },
    # Gene-Disease relationships (Orphanet, ClinGen)
    'genes_diseases': {
        'path': '/api/genes/diseases',
        'from_type': 'gene',
        'to_type': 'ontology',
        'from_params': ['gene_id', 'gene_name', 'alias', 'hgnc_id'],
        'sources': ['Orphanet', 'ClinGen'],
        'filters': {},
        'supports_verbose': True,
        'max_limit': 25,
    },
    'diseases_genes': {
        'path': '/api/diseases/genes',
        'from_type': 'ontology',
        'to_type': 'gene',
        'from_params': ['disease_name', 'disease_id'],
        'sources': ['Orphanet', 'ClinGen'],
        'filters': {},
        'supports_verbose': True,
        'max_limit': 100,
    },
    # Gene-Gene relationships (coexpression, interactions)
    'genes_genes': {
        'path': '/api/genes/genes',
        'from_type': 'gene',
        'to_type': 'gene',
        'from_params': ['gene_id', 'gene_name', 'alias', 'hgnc_id'],
        'sources': ['CoXPresdb', 'BioGRID'],
        'filters': {
            'z_score': 'range',
            'interaction_type': 'string',
        },
        'supports_verbose': False,
        'max_limit': 100,
    },
    # Protein-Protein interactions
    'proteins_proteins': {
        'path': '/api/proteins/proteins',
        'from_type': 'protein',
        'to_type': 'protein',
        'from_params': ['protein_id', 'protein_name', 'full_name', 'dbxrefs'],
        'sources': ['BioGRID'],
        'filters': {
            'interaction_type': 'string',
        },
        'supports_verbose': True,
        'max_limit': 100,
    },
    # Complex-Protein relationships
    'complexes_proteins': {
        'path': '/api/complexes/proteins',
        'from_type': 'complex',
        'to_type': 'protein',
        'from_params': ['complex_id', 'complex_name', 'description'],
        'sources': ['EBI Complex Portal'],
        'filters': {},
        'supports_verbose': True,
        'max_limit': 50,
    },
    'proteins_complexes': {
        'path': '/api/proteins/complexes',
        'from_type': 'protein',
        'to_type': 'complex',
        'from_params': ['protein_id', 'protein_name', 'full_name', 'dbxrefs'],
        'sources': ['EBI Complex Portal'],
        'filters': {},
        'supports_verbose': True,
        'max_limit': 100,
    },
    # Gene-Pathway relationships
    'genes_pathways': {
        'path': '/api/genes/pathways',
        'from_type': 'gene',
        'to_type': 'pathway',
        'from_params': ['gene_id', 'gene_name', 'alias', 'hgnc_id'],
        'sources': ['Reactome'],
        'filters': {},
        'supports_verbose': True,
        'max_limit': 100,
    },
    # Gene-Transcript relationships
    'genes_transcripts': {
        'path': '/api/genes/transcripts',
        'from_type': 'gene',
        'to_type': 'transcript',
        'from_params': ['gene_id', 'gene_name', 'alias', 'hgnc_id'],
        'sources': ['GENCODE'],
        'filters': {},
        'supports_verbose': True,
        'max_limit': 100,
    },
    'transcripts_genes': {
        'path': '/api/transcripts/genes',
        'from_type': 'transcript',
        'to_type': 'gene',
        'from_params': ['transcript_id', 'region'],
        'sources': ['GENCODE'],
        'filters': {},
        'supports_verbose': True,
        'max_limit': 100,
    },
    # Transcript-Protein relationships
    'transcripts_proteins': {
        'path': '/api/transcripts/proteins',
        'from_type': 'transcript',
        'to_type': 'protein',
        'from_params': ['transcript_id', 'transcript_type', 'region'],
        'sources': ['GENCODE'],
        'filters': {},
        'supports_verbose': True,
        'max_limit': 100,
    },
    'proteins_transcripts': {
        'path': '/api/proteins/transcripts',
        'from_type': 'protein',
        'to_type': 'transcript',
        'from_params': ['protein_id', 'protein_name', 'full_name', 'dbxrefs'],
        'sources': ['GENCODE'],
        'filters': {},
        'supports_verbose': True,
        'max_limit': 100,
    },
    # Motif-Protein relationships
    'motifs_proteins': {
        'path': '/api/motifs/proteins',
        'from_type': 'ontology',
        'to_type': 'protein',
        'from_params': ['tf_name'],
        'sources': ['HOCOMOCOv11', 'SEMpl'],
        'filters': {},
        'supports_verbose': True,
        'max_limit': 1000,
    },
    'proteins_motifs': {
        'path': '/api/proteins/motifs',
        'from_type': 'protein',
        'to_type': 'ontology',
        'from_params': ['protein_id', 'protein_name', 'full_name', 'dbxrefs'],
        'sources': ['HOCOMOCOv11', 'SEMpl'],
        'filters': {},
        'supports_verbose': True,
        'max_limit': 1000,
    },
    # Variant-Variant relationships (Linkage Disequilibrium)
    'variants_variants': {
        'path': '/api/variants/variants',
        'from_type': 'variant',
        'to_type': 'variant',
        'from_params': ['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id', 'chr', 'position'],
        'sources': ['TopLD'],
        'filters': {
            'r2': 'range',
            'd_prime': 'range',
            'ancestry': 'enum',
        },
        'supports_verbose': True,
        'max_limit': 500,
    },
    # Variant-Coding Variant relationships
    'variants_coding_variants': {
        'path': '/api/variants/coding-variants',
        'from_type': 'variant',
        'to_type': 'coding_variant',
        'from_params': ['variant_id', 'spdi', 'hgvs', 'ca_id'],
        'sources': ['dbNSFP'],
        'filters': {
            'files_fileset': 'string',
        },
        'supports_verbose': False,
        'max_limit': 500,
    },
    'coding_variants_variants': {
        'path': '/api/coding-variants/variants',
        'from_type': 'coding_variant',
        'to_type': 'variant',
        'from_params': ['coding_variant_name', 'hgvsp'],
        'sources': ['dbNSFP'],
        'filters': {},
        'supports_verbose': False,
        'max_limit': 500,
    },
    # Variant-Genomic Element relationships (MPRA, caQTL)
    'variants_genomic_elements': {
        'path': '/api/variants/genomic-elements',
        'from_type': 'variant',
        'to_type': 'genomic_element',
        'from_params': ['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id'],
        'sources': ['AFGR', 'IGVF'],
        'methods': ['BlueSTARR', 'lentiMPRA', 'caQTL'],
        'filters': {
            'files_fileset': 'string',
            'log10pvalue': 'range',
        },
        'supports_verbose': True,
        'max_limit': 100,
    },
    # Genomic Element-Gene relationships (E2G CRISPR)
    'genomic_elements_genes': {
        'path': '/api/genomic-elements/genes',
        'from_type': 'genomic_element',
        'to_type': 'gene',
        'from_params': ['region'],
        'sources': ['ENCODE_EpiRaction', 'ENCODE-E2G-DNaseOnly', 'ENCODE-E2G-Full', 'ENCODE-E2G-CRISPR'],
        'methods': ['CRISPR FACS screen', 'Perturb-seq', 'ENCODE-rE2G'],
        'filters': {
            'source_annotation': 'string',
            'region_type': 'string',
            'biosample_id': 'string',
            'biosample_name': 'string',
            'biosample_synonyms': 'string',
            'files_fileset': 'string',
        },
        'supports_verbose': True,
        'max_limit': 500,
    },
    # Genomic Element-Biosample relationships (MPRA)
    'genomic_elements_biosamples': {
        'path': '/api/genomic-elements/biosamples',
        'from_type': 'genomic_element',
        'to_type': 'ontology',
        'from_params': ['region'],
        'sources': ['IGVF'],
        'methods': ['lentiMPRA', 'MPRA'],
        'filters': {
            'files_fileset': 'string',
        },
        'supports_verbose': True,
        'max_limit': 100,
    },
    'biosamples_genomic_elements': {
        'path': '/api/biosamples/genomic-elements',
        'from_type': 'ontology',
        'to_type': 'genomic_element',
        'from_params': ['biosample_id', 'biosample_name', 'biosample_synonyms'],
        'sources': ['IGVF'],
        'filters': {},
        'supports_verbose': True,
        'max_limit': 50,
    },
    # GO term annotations
    'go_terms_annotations': {
        'path': '/api/annotations/go-terms',
        'from_type': 'protein',
        'to_type': 'ontology',
        'from_params': ['query'],  # Can be protein or transcript ID
        'sources': ['Gene Ontology'],
        'filters': {
            'name': 'enum',  # 'involved in', 'is located in', 'has the function'
        },
        'supports_verbose': False,
        'max_limit': 100,
    },
}


# Relationship type to endpoint mapping for higher-level abstractions
RELATIONSHIP_TYPE_MAPPING = {
    'regulatory': {
        'gene': ['genes_variants', 'genomic_elements_genes'],
        'variant': ['variants_genes', 'variants_genomic_elements'],
        'genomic_element': ['genomic_elements_genes'],
    },
    'genetic': {
        'gene': ['genes_diseases'],
        'variant': ['variants_phenotypes', 'variants_diseases'],
        'ontology': ['phenotypes_variants', 'diseases_genes'],
    },
    'physical': {
        'protein': ['proteins_proteins', 'proteins_complexes'],
        'complex': ['complexes_proteins'],
        'gene': ['genes_genes'],
    },
    'functional': {
        'gene': ['genes_pathways'],
        'protein': ['go_terms_annotations'],
    },
    'pharmacological': {
        'variant': ['variants_drugs'],
        'drug': ['drugs_variants'],
    },
    'ld': {
        'variant': ['variants_variants'],
    },
    'coding': {
        'variant': ['variants_coding_variants'],
        'coding_variant': ['coding_variants_variants'],
    },
    'transcription': {
        'gene': ['genes_transcripts'],
        'transcript': ['transcripts_genes', 'transcripts_proteins'],
        'protein': ['proteins_transcripts'],
    },
}


def get_edge_config(endpoint_key: str) -> EdgeEndpointConfig | None:
    """Get configuration for a specific edge endpoint."""
    return EDGE_ENDPOINTS.get(endpoint_key)


def get_endpoints_for_entity_and_relationship(
    entity_type: EntityType, relationship_type: str
) -> list[str]:
    """
    Get applicable endpoint keys for an entity type and relationship type.

    Args:
        entity_type: Type of the starting entity
        relationship_type: Type of relationship to find

    Returns:
        List of endpoint keys that match the criteria
    """
    if relationship_type not in RELATIONSHIP_TYPE_MAPPING:
        return []

    entity_mapping = RELATIONSHIP_TYPE_MAPPING[relationship_type]
    return entity_mapping.get(entity_type, [])


def get_all_sources() -> set[str]:
    """Get all unique data sources across all endpoints."""
    sources = set()
    for config in EDGE_ENDPOINTS.values():
        if 'sources' in config:
            sources.update(config['sources'])
    return sources


def get_sources_by_category() -> dict[str, list[str]]:
    """Organize sources by category for the list_sources tool."""
    return {
        'variant_annotations': ['dbNSFP', 'ClinGen'],
        'gene_expression': ['AFGR', 'EBI eQTL Catalogue', 'IGVF'],
        'regulatory': ['ADASTRA', 'GVATdb', 'SEMVAR', 'ENCODE_SCREEN', 'ENCODE-E2G-DNaseOnly',
                       'ENCODE-E2G-Full', 'ENCODE-E2G-CRISPR', 'ENCODE_EpiRaction'],
        'disease': ['Orphanet', 'ClinGen', 'OpenTargets'],
        'drugs': ['PharmGKB'],
        'interactions': ['BioGRID', 'CoXPresdb', 'EBI Complex Portal'],
        'studies': ['GWAS Catalog', 'OpenTargets'],
        'structure': ['GENCODE'],
        'linkage': ['TopLD'],
        'motifs': ['HOCOMOCOv11', 'SEMpl'],
        'pathways': ['Reactome'],
        'ontology': ['Gene Ontology'],
    }
