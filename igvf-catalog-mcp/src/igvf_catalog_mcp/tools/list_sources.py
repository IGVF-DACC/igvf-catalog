"""List sources tool - discover available data sources and methods."""

import json
from typing import Any

from mcp.types import Tool, TextContent

from ..services.formatter import format_error


# Tool definition
LIST_SOURCES_TOOL = Tool(
    name='list_sources',
    description=(
        'Discover available data sources, methods, and filter options in the IGVF Catalog. '
        'Helps find valid values for source and method filters in other tools. '
        'Categories: variant_annotations, gene_expression, regulatory, disease, drugs, interactions, studies.'
    ),
    inputSchema={
        'type': 'object',
        'properties': {
            'category': {
                'type': 'string',
                'description': 'Category of data sources to list (optional)',
                'enum': [
                    'variant_annotations',
                    'gene_expression',
                    'regulatory',
                    'disease',
                    'drugs',
                    'interactions',
                    'studies',
                ],
            },
        },
    },
)


# Data source information (curated based on IGVF Catalog docs)
DATA_SOURCES = {
    'variant_annotations': {
        'description': 'Sources for variant annotations and functional predictions',
        'sources': [
            {
                'name': 'FAVOR',
                'description': 'Functional annotation of variants (BRAVO, gnomAD, CADD scores)',
                'data_types': ['allele frequencies', 'CADD scores', 'functional categories'],
            },
            {
                'name': 'dbSNFP',
                'description': 'Database of human nonsynonymous SNPs and their functional predictions',
                'data_types': ['coding variant annotations', 'pathogenicity predictions'],
            },
            {
                'name': 'ClinGen',
                'description': 'Clinical genome resource for variant-disease associations',
                'data_types': ['pathogenic variants', 'variant-disease relationships'],
            },
        ],
    },
    'gene_expression': {
        'description': 'Sources for gene expression and QTL data',
        'sources': [
            {
                'name': 'GTEx',
                'description': 'Genotype-Tissue Expression project',
                'data_types': ['eQTLs', 'sQTLs', 'tissue-specific expression'],
            },
            {
                'name': 'AFGR',
                'description': 'Aggregated Functional Genomics Resource',
                'data_types': ['eQTLs', 'sQTLs', 'regulatory variants'],
            },
            {
                'name': 'EBI eQTL Catalogue',
                'description': "EBI's eQTL catalog across multiple studies",
                'data_types': ['eQTLs', 'molecular QTLs'],
            },
            {
                'name': 'IGVF',
                'description': 'Impact of Genomic Variation on Function consortium data',
                'data_types': ['MPRA', 'CRISPR screens', 'regulatory variants'],
                'methods': ['Variant-EFFECTS', 'STARR-seq', 'lentiMPRA', 'BlueSTARR'],
            },
        ],
    },
    'regulatory': {
        'description': 'Sources for regulatory element and enhancer data',
        'sources': [
            {
                'name': 'ENCODE',
                'description': 'Encyclopedia of DNA Elements',
                'data_types': ['regulatory elements', 'enhancers', 'TF binding', 'chromatin accessibility'],
                'methods': ['ENCODE-E2G-DNaseOnly', 'ENCODE-E2G-Full', 'ENCODE-E2G-CRISPR'],
            },
            {
                'name': 'ENCODE_SCREEN',
                'description': 'ENCODE cis-regulatory elements',
                'data_types': ['candidate cis-regulatory elements (cCREs)', 'chromatin states'],
            },
            {
                'name': 'ADASTRA',
                'description': 'Allele-specific TF binding from ChIP-seq',
                'data_types': ['allele-specific TF binding'],
            },
            {
                'name': 'GVATdb',
                'description': 'Genome Variation and TF binding database',
                'data_types': ['variant effects on TF binding'],
            },
            {
                'name': 'SEMVAR',
                'description': 'Predicted allele-specific binding',
                'data_types': ['variant effects on TF binding', 'SEMpl predictions'],
            },
        ],
    },
    'disease': {
        'description': 'Sources for disease-gene associations',
        'sources': [
            {
                'name': 'Orphanet',
                'description': 'Rare disease and gene associations',
                'data_types': ['disease-gene relationships', 'rare diseases'],
            },
            {
                'name': 'ClinGen',
                'description': 'Clinical genome resource',
                'data_types': ['gene-disease validity', 'pathogenic variants'],
            },
            {
                'name': 'GWAS Catalog',
                'description': 'Genome-wide association studies',
                'data_types': ['variant-phenotype associations', 'complex traits'],
            },
        ],
    },
    'drugs': {
        'description': 'Sources for pharmacogenomics data',
        'sources': [
            {
                'name': 'PharmGKB',
                'description': 'Pharmacogenomics Knowledgebase',
                'data_types': ['drug-variant associations', 'pharmacogenomics'],
            },
        ],
    },
    'interactions': {
        'description': 'Sources for molecular interactions',
        'sources': [
            {
                'name': 'BioGRID',
                'description': 'Biological General Repository for Interaction Datasets',
                'data_types': ['protein-protein interactions', 'genetic interactions', 'gene-gene coexpression'],
            },
            {
                'name': 'CoXPresdb',
                'description': 'Coexpression database',
                'data_types': ['gene-gene coexpression'],
            },
            {
                'name': 'EBI Complex Portal',
                'description': 'Manually curated protein complexes',
                'data_types': ['protein complexes'],
            },
        ],
    },
    'studies': {
        'description': 'Study collections and datasets',
        'sources': [
            {
                'name': 'GWAS Catalog',
                'description': 'Genome-wide association studies',
                'data_types': ['GWAS summary statistics'],
            },
            {
                'name': 'VAMP-seq',
                'description': 'Variant Effect on Activity Measured by MPRA',
                'data_types': ['variant functional assays', 'MPRA'],
            },
            {
                'name': 'MorPhiC',
                'description': 'Molecular Phenotypes of Human Cells',
                'data_types': ['CRISPR screens', 'functional genomics'],
            },
        ],
    },
}


async def list_sources(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute the list_sources tool.

    Args:
        arguments: Tool arguments with optional 'category'

    Returns:
        List of TextContent with available data sources
    """
    try:
        category = arguments.get('category')

        if category:
            # Return specific category
            if category not in DATA_SOURCES:
                return [
                    TextContent(
                        type='text',
                        text=f'Unknown category: {category}. '
                        f"Valid categories: {', '.join(DATA_SOURCES.keys())}",
                    )
                ]

            response_data = {
                'category': category,
                **DATA_SOURCES[category],
            }
        else:
            # Return all categories
            response_data = {
                'categories': list(DATA_SOURCES.keys()),
                'sources_by_category': DATA_SOURCES,
            }

        response_text = json.dumps(response_data, indent=2)

        return [
            TextContent(
                type='text',
                text=response_text,
            )
        ]

    except Exception as e:
        return [
            TextContent(
                type='text',
                text=f'Error listing sources: {format_error(e)}',
            )
        ]
