"""Search region tool - find entities in a genomic region."""

import asyncio
import json
from typing import Any

from mcp.types import Tool, TextContent

from ..services.api_client import IGVFCatalogClient
from ..services.region_parser import RegionParser
from ..services.formatter import format_error


# Tool definition
SEARCH_REGION_TOOL = Tool(
    name='search_region',
    description=(
        'Find all biological entities within a genomic region. '
        'Searches genes, variants, and regulatory elements in parallel. '
        "Supports flexible region formats: 'chr1:1000-2000', '1:1M-2M', 'chrX:1,000,000-2,000,000'. "
        'Returns genes, variants, and regulatory elements found in the region.'
    ),
    inputSchema={
        'type': 'object',
        'properties': {
            'region': {
                'type': 'string',
                'description': "Genomic region (e.g., 'chr1:1000000-2000000' or '1:1M-2M')",
            },
            'include': {
                'type': 'array',
                'items': {'type': 'string', 'enum': ['genes', 'variants', 'regulatory_elements']},
                'description': 'Entity types to include (default: all)',
            },
            'organism': {
                'type': 'string',
                'description': 'Organism name',
                'enum': ['Homo sapiens', 'Mus musculus'],
                'default': 'Homo sapiens',
            },
            'limit': {
                'type': 'integer',
                'description': 'Maximum results per entity type (default: 25)',
                'minimum': 1,
                'maximum': 500,
                'default': 25,
            },
        },
        'required': ['region'],
    },
)


async def search_region(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute the search_region tool.

    Args:
        arguments: Tool arguments with 'region' and optional filters

    Returns:
        List of TextContent with entities found in the region
    """
    try:
        region_str = arguments['region']
        include = arguments.get(
            'include', ['genes', 'variants', 'regulatory_elements'])
        organism = arguments.get('organism', 'Homo sapiens')
        limit = arguments.get('limit', 25)

        # Parse and validate the region
        region = RegionParser.parse_region(region_str)

        # Warn if region is very large (> 10 Mb)
        region_size = region.end - region.start
        if region_size > 10_000_000:
            warning = f'Warning: Large region ({region_size:,} bp). Results may be incomplete.\n\n'
        else:
            warning = ''

        # Build queries for different entity types
        queries = {}

        if 'genes' in include:
            queries['genes'] = ('/api/genes', str(region))

        if 'variants' in include:
            queries['variants'] = ('/api/variants', str(region))

        if 'regulatory_elements' in include:
            queries['regulatory_elements'] = (
                '/api/genomic-elements', str(region))

        # Execute queries in parallel
        async with IGVFCatalogClient() as client:
            tasks = {
                entity_type: client.search_region(
                    endpoint=endpoint,
                    region_str=region_str_query,
                    organism=organism,
                    limit=limit,
                )
                for entity_type, (endpoint, region_str_query) in queries.items()
            }

            results = await asyncio.gather(*tasks.values(), return_exceptions=True)

            # Combine results
            response = {}
            for entity_type, result in zip(tasks.keys(), results):
                if isinstance(result, Exception):
                    response[entity_type] = {'error': str(result)}
                else:
                    response[entity_type] = result

        # Format response
        response_data = {
            'region': str(region),
            'region_size_bp': region_size,
            'organism': organism,
            'results': response,
        }

        response_text = warning + json.dumps(response_data, indent=2)

        return [
            TextContent(
                type='text',
                text=response_text,
            )
        ]

    except ValueError as e:
        # Region parsing errors
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
                text=f'Error searching region: {format_error(e)}',
            )
        ]
