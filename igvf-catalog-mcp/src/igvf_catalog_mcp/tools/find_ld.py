"""Find linkage disequilibrium (LD) tool - discover variants in LD with a query variant."""

import json
from typing import Any

from mcp.types import Tool, TextContent

from ..services.api_client import IGVFCatalogClient
from ..services.id_parser import IDParser
from ..services.formatter import format_error


# Tool definition
FIND_LD_TOOL = Tool(
    name='find_ld',
    description=(
        'Find variants in linkage disequilibrium (LD) with a query variant. '
        'LD measures the non-random association of alleles at different loci. '
        'Returns variants with their r² and D\' statistics across different populations. '
        'Useful for fine-mapping GWAS signals and identifying proxy SNPs.'
    ),
    inputSchema={
        'type': 'object',
        'properties': {
            'variant_id': {
                'type': 'string',
                'description': "Variant identifier (e.g., 'rs12345', 'NC_000011.10:9083634:A:T')",
            },
            'r2_threshold': {
                'type': 'number',
                'description': 'Minimum r² value (0-1). Common thresholds: 0.8 (strong LD), 0.5 (moderate LD)',
                'minimum': 0,
                'maximum': 1,
                'default': 0.8,
            },
            'd_prime_threshold': {
                'type': 'number',
                'description': 'Minimum D\' value (0-1). Optional, can be used with or without r²',
                'minimum': 0,
                'maximum': 1,
            },
            'ancestry': {
                'type': 'string',
                'description': 'Population ancestry for LD calculation',
                'enum': ['AFR', 'AMR', 'EAS', 'EUR', 'SAS'],
                'default': 'EUR',
            },
            'limit': {
                'type': 'integer',
                'description': 'Maximum number of results (default: 100)',
                'minimum': 1,
                'maximum': 500,
                'default': 100,
            },
            'verbose': {
                'type': 'boolean',
                'description': 'Return full variant details (default: false)',
                'default': False,
            },
        },
        'required': ['variant_id'],
    },
)


async def find_ld(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute the find_ld tool.

    Args:
        arguments: Tool arguments with variant_id, thresholds, and ancestry

    Returns:
        List of TextContent with LD results
    """
    try:
        variant_id = arguments['variant_id']
        r2_threshold = arguments.get('r2_threshold', 0.8)
        d_prime_threshold = arguments.get('d_prime_threshold')
        ancestry = arguments.get('ancestry', 'EUR')
        limit = arguments.get('limit', 100)
        verbose = arguments.get('verbose', False)

        # Detect variant type and normalize ID
        entity_type, param_name = IDParser.detect_entity_type(variant_id)

        if entity_type != 'variant':
            return [
                TextContent(
                    type='text',
                    text=f'Error: Expected a variant ID, but got {entity_type}. '
                    f'Please provide a valid variant identifier (rsID, SPDI, HGVS, or ClinGen Allele ID).',
                )
            ]

        normalized_id = IDParser.normalize_identifier(variant_id, entity_type)

        # Build query parameters
        params = {
            param_name: normalized_id,
            'r2': f'gte:{r2_threshold}',
            'ancestry': ancestry,
            'limit': min(limit, 500),
            'page': 0,
        }

        # Add D' threshold if provided
        if d_prime_threshold is not None:
            params['d_prime'] = f'gte:{d_prime_threshold}'

        # Add verbose mode
        if verbose:
            params['verbose'] = 'true'

        # Query the API
        async with IGVFCatalogClient() as client:
            ld_results = await client.find_associations(
                endpoint='/api/variants/variants', params=params, verbose=verbose
            )

        # Process results
        if not ld_results:
            return [
                TextContent(
                    type='text',
                    text=json.dumps(
                        {
                            'query_variant': normalized_id,
                            'param_used': param_name,
                            'ancestry': ancestry,
                            'r2_threshold': r2_threshold,
                            'd_prime_threshold': d_prime_threshold,
                            'num_ld_variants': 0,
                            'ld_variants': [],
                            'message': f'No variants in LD found with r² ≥ {r2_threshold} in {ancestry} population',
                        },
                        indent=2,
                    ),
                )
            ]

        # Format response
        response_data = {
            'query_variant': normalized_id,
            'param_used': param_name,
            'ancestry': ancestry,
            'filters_applied': {
                'r2_min': r2_threshold,
                'd_prime_min': d_prime_threshold,
            },
            'num_ld_variants': len(ld_results),
            'ld_variants': ld_results,
            'summary': {
                'strong_ld_count': len([v for v in ld_results if v.get('r2', 0) >= 0.8]),
                'moderate_ld_count': len([v for v in ld_results if 0.5 <= v.get('r2', 0) < 0.8]),
                'weak_ld_count': len([v for v in ld_results if v.get('r2', 0) < 0.5]),
            },
        }

        response_text = json.dumps(response_data, indent=2)

        return [
            TextContent(
                type='text',
                text=response_text,
            )
        ]

    except ValueError as e:
        # ID parsing errors
        return [
            TextContent(
                type='text',
                text=format_error(e),
            )
        ]
    except Exception as e:
        # API errors or other issues
        return [
            TextContent(
                type='text',
                text=f'Error finding LD variants: {format_error(e)}',
            )
        ]
