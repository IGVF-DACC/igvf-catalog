"""Find associations tool - discover relationships between entities."""

import json
from typing import Any

from mcp.types import Tool, TextContent

from ..services.api_client import IGVFCatalogClient
from ..services.id_parser import IDParser
from ..services.formatter import format_error


# Tool definition
FIND_ASSOCIATIONS_TOOL = Tool(
    name='find_associations',
    description=(
        'Find connections between entities in the knowledge graph. '
        'Discovers eQTLs, GWAS associations, protein interactions, pathways, and more. '
        "Relationship types: 'regulatory' (eQTLs, enhancer-gene), 'genetic' (GWAS, disease-gene), "
        "'physical' (protein-protein), 'functional' (pathways, GO terms), 'pharmacological' (drug-variant). "
        'Returns detailed associations with p-values, effect sizes, and sources.'
    ),
    inputSchema={
        'type': 'object',
        'properties': {
            'entity_id': {
                'type': 'string',
                'description': "Starting entity ID (e.g., 'TP53', 'rs12345', 'ENSG00000141510')",
            },
            'relationship': {
                'type': 'string',
                'description': 'Type of relationship to find',
                'enum': ['regulatory', 'genetic', 'physical', 'functional', 'pharmacological', 'all'],
            },
            'filters': {
                'type': 'object',
                'description': 'Optional filters',
                'properties': {
                    'p_value': {'type': 'number', 'description': 'Maximum p-value threshold'},
                    'source': {'type': 'string', 'description': "Data source (e.g., 'GTEx', 'GWAS Catalog')"},
                    'tissue': {'type': 'string', 'description': 'Tissue or cell type'},
                },
            },
            'limit': {
                'type': 'integer',
                'description': 'Maximum number of results (default: 25)',
                'minimum': 1,
                'maximum': 500,
                'default': 25,
            },
        },
        'required': ['entity_id', 'relationship'],
    },
)


# Relationship type to API endpoints mapping
RELATIONSHIP_ENDPOINTS = {
    'regulatory': {
        'gene': ['/api/genes/variants', '/api/genomic-elements/genes'],
        'variant': ['/api/variants/genes', '/api/variants/genomic-elements'],
    },
    'genetic': {
        'gene': ['/api/genes/diseases'],
        'variant': ['/api/variants/phenotypes', '/api/variants/diseases'],
    },
    'physical': {
        'protein': ['/api/proteins/proteins'],
        'complex': ['/api/complexes/proteins'],
    },
    'functional': {
        'gene': ['/api/genes/pathways'],
        'protein': ['/api/go/annotations'],
    },
    'pharmacological': {
        'variant': ['/api/variants/drugs'],
        'drug': ['/api/drugs/variants'],
    },
}


async def find_associations(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute the find_associations tool.

    Args:
        arguments: Tool arguments with entity_id, relationship, and optional filters

    Returns:
        List of TextContent with associations found
    """
    try:
        entity_id = arguments['entity_id']
        relationship = arguments['relationship']
        filters = arguments.get('filters', {})
        limit = arguments.get('limit', 25)

        # Detect entity type
        entity_type, param_name = IDParser.detect_entity_type(entity_id)
        normalized_id = IDParser.normalize_identifier(entity_id, entity_type)

        # Determine which endpoints to query
        if relationship == 'all':
            # Get all applicable relationship types for this entity
            endpoints_to_query = []
            for rel_type, entity_map in RELATIONSHIP_ENDPOINTS.items():
                if entity_type in entity_map:
                    endpoints_to_query.extend(entity_map[entity_type])
        else:
            # Get endpoints for specific relationship type
            if relationship not in RELATIONSHIP_ENDPOINTS:
                return [
                    TextContent(
                        type='text',
                        text=f'Unknown relationship type: {relationship}. '
                        f"Valid types: {', '.join(RELATIONSHIP_ENDPOINTS.keys())}, all",
                    )
                ]

            entity_map = RELATIONSHIP_ENDPOINTS[relationship]
            if entity_type not in entity_map:
                return [
                    TextContent(
                        type='text',
                        text=f"Relationship type '{relationship}' not applicable to {entity_type} entities.",
                    )
                ]

            endpoints_to_query = entity_map[entity_type]

        # Build query parameters
        params = {
            param_name: normalized_id,
            'limit': limit,
        }

        # Add filters
        if 'p_value' in filters:
            # Convert to -log10
            params['log10pvalue'] = f"lte:{-1 * filters['p_value']}"
        if 'source' in filters:
            params['source'] = filters['source']
        if 'tissue' in filters:
            params['biological_context'] = filters['tissue']

        # Query all applicable endpoints
        all_associations = []
        async with IGVFCatalogClient() as client:
            for endpoint in endpoints_to_query:
                try:
                    associations = await client.find_associations(
                        endpoint=endpoint,
                        params=params,
                        verbose=False,
                    )

                    # Add endpoint info to each association
                    for assoc in associations:
                        assoc['_endpoint'] = endpoint

                    all_associations.extend(associations)
                except Exception as e:
                    # Log error but continue with other endpoints
                    all_associations.append({
                        'error': f'Error querying {endpoint}: {str(e)}',
                        '_endpoint': endpoint,
                    })

        # Format response
        response_data = {
            'entity_id': normalized_id,
            'entity_type': entity_type,
            'relationship_type': relationship,
            'num_associations': len([a for a in all_associations if 'error' not in a]),
            'associations': all_associations,
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
                text=f'Error finding associations: {format_error(e)}',
            )
        ]
