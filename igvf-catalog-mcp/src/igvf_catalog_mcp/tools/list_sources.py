"""List sources tool - discover available data sources and methods."""

import json
from typing import Any

from mcp.types import Tool, TextContent

from ..services.formatter import format_error
from ..services.edge_config import get_sources_by_category, get_edge_config, EDGE_ENDPOINTS


# Tool definition
LIST_SOURCES_TOOL = Tool(
    name='list_sources',
    description=(
        'Discover available data sources, methods, and filter options in the IGVF Catalog. '
        'Helps find valid values for source and method filters in other tools. '
        'Categories: variant_annotations, gene_expression, regulatory, disease, drugs, '
        'interactions, studies, structure, linkage, motifs, pathways, ontology.'
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
                    'structure',
                    'linkage',
                    'motifs',
                    'pathways',
                    'ontology',
                ],
            },
            'endpoint': {
                'type': 'string',
                'description': 'Specific endpoint to get source/method information for (optional)',
            },
        },
    },
)


# Data source descriptions (curated)
SOURCE_DESCRIPTIONS = {
    'FAVOR': 'Functional annotation of variants (BRAVO, gnomAD, CADD scores)',
    'dbNSFP': 'Database of human nonsynonymous SNPs and their functional predictions',
    'ClinGen': 'Clinical genome resource for variant-disease associations',
    'AFGR': 'Aggregated Functional Genomics Resource - eQTLs, sQTLs',
    'EBI eQTL Catalogue': "EBI's eQTL catalog across multiple studies",
    'IGVF': 'Impact of Genomic Variation on Function consortium data',
    'ADASTRA': 'Allele-specific TF binding from ChIP-seq',
    'GVATdb': 'Genome Variation and TF binding database',
    'UKB': 'UK Biobank - pQTL data',
    'SEMVAR': 'Predicted allele-specific binding (SEMpl predictions)',
    'ENCODE_SCREEN': 'ENCODE cis-regulatory elements',
    'ENCODE-E2G-DNaseOnly': 'ENCODE enhancer-gene predictions (DNase-based)',
    'ENCODE-E2G-Full': 'ENCODE enhancer-gene predictions (full model)',
    'ENCODE-E2G-CRISPR': 'ENCODE CRISPR-validated enhancer-gene links',
    'ENCODE_EpiRaction': 'ENCODE EpiRaction enhancer predictions',
    'OpenTargets': 'Open Targets GWAS catalog',
    'PharmGKB': 'Pharmacogenomics Knowledgebase',
    'Orphanet': 'Rare disease and gene associations',
    'BioGRID': 'Biological General Repository for Interaction Datasets',
    'CoXPresdb': 'Gene-gene coexpression database',
    'EBI Complex Portal': 'Manually curated protein complexes',
    'Reactome': 'Reactome pathway database',
    'GENCODE': 'GENCODE gene annotation',
    'TopLD': 'TopLD linkage disequilibrium database',
    'HOCOMOCOv11': 'HOCOMOCO transcription factor binding motif database',
    'SEMpl': 'SEMpl TF binding predictions',
    'Gene Ontology': 'Gene Ontology annotations',
}


def get_category_details(category: str) -> dict[str, Any]:
    """Get detailed information about sources in a category."""
    sources_by_category = get_sources_by_category()

    if category not in sources_by_category:
        return {}

    sources = sources_by_category[category]

    return {
        'category': category,
        'sources': [
            {
                'name': source,
                'description': SOURCE_DESCRIPTIONS.get(source, 'No description available'),
            }
            for source in sources
        ],
    }


def get_endpoint_details(endpoint_key: str) -> dict[str, Any]:
    """Get detailed information about a specific endpoint."""
    config = get_edge_config(endpoint_key)

    if not config:
        return {}

    details = {
        'endpoint': endpoint_key,
        'path': config.get('path'),
        'from_type': config.get('from_type'),
        'to_type': config.get('to_type'),
    }

    if 'sources' in config:
        details['sources'] = [
            {
                'name': source,
                'description': SOURCE_DESCRIPTIONS.get(source, 'No description available'),
            }
            for source in config['sources']
        ]

    if 'methods' in config:
        details['methods'] = config['methods']

    if 'labels' in config:
        details['labels'] = config['labels']

    if 'filters' in config:
        details['filters'] = config['filters']

    details['max_limit'] = config.get('max_limit', 100)
    details['supports_verbose'] = config.get('supports_verbose', False)

    return details


async def list_sources(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute the list_sources tool.

    Args:
        arguments: Tool arguments with optional 'category' or 'endpoint'

    Returns:
        List of TextContent with available data sources
    """
    try:
        category = arguments.get('category')
        endpoint = arguments.get('endpoint')

        if endpoint:
            # Return details for a specific endpoint
            response_data = get_endpoint_details(endpoint)
            if not response_data:
                return [
                    TextContent(
                        type='text',
                        text=f'Unknown endpoint: {endpoint}. '
                        f"Available endpoints: {', '.join(EDGE_ENDPOINTS.keys())}",
                    )
                ]
        elif category:
            # Return specific category
            sources_by_category = get_sources_by_category()
            if category not in sources_by_category:
                return [
                    TextContent(
                        type='text',
                        text=f'Unknown category: {category}. '
                        f"Valid categories: {', '.join(sources_by_category.keys())}",
                    )
                ]

            response_data = get_category_details(category)
        else:
            # Return all categories overview
            sources_by_category = get_sources_by_category()
            response_data = {
                'categories': list(sources_by_category.keys()),
                'total_sources': len(set(source for sources in sources_by_category.values() for source in sources)),
                'total_endpoints': len(EDGE_ENDPOINTS),
                'sources_by_category': {
                    cat: [
                        {
                            'name': source,
                            'description': SOURCE_DESCRIPTIONS.get(source, 'No description available'),
                        }
                        for source in sources
                    ]
                    for cat, sources in sources_by_category.items()
                },
                'usage_hint': 'Use category parameter to get details for a specific category, '
                'or endpoint parameter to get details for a specific edge endpoint.',
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
