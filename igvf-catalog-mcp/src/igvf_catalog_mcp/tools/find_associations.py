"""Find associations tool - discover relationships between entities."""

import json
from typing import Any

from mcp.types import Tool, TextContent

from ..services.api_client import IGVFCatalogClient
from ..services.id_parser import IDParser
from ..services.formatter import format_error
from ..services.edge_config import (
    get_endpoints_for_entity_and_relationship,
    get_edge_config,
    RELATIONSHIP_TYPE_MAPPING,
)


# Tool definition
FIND_ASSOCIATIONS_TOOL = Tool(
    name='find_associations',
    description=(
        'Find connections between entities in the knowledge graph. '
        'Discovers eQTLs, GWAS associations, protein interactions, pathways, and more. '
        "Relationship types: 'regulatory' (eQTLs, enhancer-gene), 'genetic' (GWAS, disease-gene), "
        "'physical' (protein-protein), 'functional' (pathways, GO terms), 'pharmacological' (drug-variant), "
        "'ld' (linkage disequilibrium), 'coding' (coding variant effects), 'transcription' (gene-transcript-protein). "
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
                'enum': list(RELATIONSHIP_TYPE_MAPPING.keys()) + ['all'],
            },
            'filters': {
                'type': 'object',
                'description': 'Optional filters',
                'properties': {
                    'p_value': {'type': 'number', 'description': 'Maximum p-value threshold'},
                    'source': {'type': 'string', 'description': "Data source (e.g., 'AFGR', 'EBI eQTL Catalogue')"},
                    'biological_context': {'type': 'string', 'description': 'Tissue or cell type'},
                    'method': {'type': 'string', 'description': 'Experimental method'},
                    'label': {'type': 'string', 'description': 'Edge label/type'},
                    'r2': {'type': 'number', 'description': 'LD r2 threshold (for LD queries)'},
                    'd_prime': {'type': 'number', 'description': 'LD D\' threshold (for LD queries)'},
                    'ancestry': {'type': 'string', 'description': 'Population ancestry (for LD queries)'},
                },
            },
            'limit': {
                'type': 'integer',
                'description': 'Maximum number of results (default: 25)',
                'minimum': 1,
                'maximum': 500,
                'default': 25,
            },
            'verbose': {
                'type': 'boolean',
                'description': 'Return full entity details (default: false)',
                'default': False,
            },
        },
        'required': ['entity_id', 'relationship'],
    },
)


def build_query_params(
    entity_id: str,
    param_name: str,
    edge_config: dict[str, Any],
    user_filters: dict[str, Any],
    limit: int,
    verbose: bool,
) -> dict[str, Any]:
    """
    Build query parameters for an edge endpoint based on its configuration.

    Args:
        entity_id: The normalized entity identifier
        param_name: The parameter name for this entity type at this endpoint
        edge_config: The edge endpoint configuration
        user_filters: User-provided filters
        limit: Result limit
        verbose: Whether to request verbose output

    Returns:
        Dictionary of query parameters
    """
    params = {
        param_name: entity_id,
        'limit': min(limit, edge_config.get('max_limit', 500)),
        'page': 0,
    }

    # Add verbose mode if supported
    if edge_config.get('supports_verbose', False) and verbose:
        params['verbose'] = 'true'

    # Process filters based on endpoint configuration
    if 'filters' in edge_config:
        supported_filters = edge_config['filters']

        for filter_name, filter_value in user_filters.items():
            if filter_name not in supported_filters:
                continue

            filter_type = supported_filters[filter_name]

            if filter_type == 'range':
                # Range filters need special formatting for the API
                if filter_name == 'p_value' and 'log10pvalue' in supported_filters:
                    # Convert p-value to -log10 format
                    # User provides max p-value, API expects min -log10(p-value)
                    import math
                    if filter_value > 0:
                        min_log10 = -math.log10(filter_value)
                        params['log10pvalue'] = f'gte:{min_log10:.2f}'
                elif filter_name in ['r2', 'd_prime', 'z_score']:
                    # These are typically min thresholds
                    params[filter_name] = f'gte:{filter_value}'
                else:
                    # Generic range filter
                    params[filter_name] = filter_value
            elif filter_type in ['string', 'enum']:
                # Direct string/enum filters
                params[filter_name] = filter_value

    # Validate and add source filter
    if 'source' in user_filters and 'sources' in edge_config:
        source = user_filters['source']
        if source in edge_config['sources']:
            params['source'] = source

    # Validate and add method filter
    if 'method' in user_filters and 'methods' in edge_config:
        method = user_filters['method']
        if method in edge_config['methods']:
            params['method'] = method

    # Validate and add label filter
    if 'label' in user_filters and 'labels' in edge_config:
        label = user_filters['label']
        if label in edge_config['labels']:
            params['label'] = label

    return params


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
        verbose = arguments.get('verbose', False)

        # Detect entity type
        entity_type, param_name = IDParser.detect_entity_type(entity_id)
        normalized_id = IDParser.normalize_identifier(entity_id, entity_type)

        # Determine which endpoints to query
        if relationship == 'all':
            # Get all applicable relationship types for this entity
            endpoint_keys = []
            for rel_type, entity_map in RELATIONSHIP_TYPE_MAPPING.items():
                if entity_type in entity_map:
                    endpoint_keys.extend(entity_map[entity_type])
        else:
            # Get endpoints for specific relationship type
            if relationship not in RELATIONSHIP_TYPE_MAPPING:
                return [
                    TextContent(
                        type='text',
                        text=f'Unknown relationship type: {relationship}. '
                        f"Valid types: {', '.join(RELATIONSHIP_TYPE_MAPPING.keys())}, all",
                    )
                ]

            endpoint_keys = get_endpoints_for_entity_and_relationship(
                entity_type, relationship)

            if not endpoint_keys:
                return [
                    TextContent(
                        type='text',
                        text=f"Relationship type '{relationship}' not applicable to {entity_type} entities.",
                    )
                ]

        # Query all applicable endpoints
        all_associations = []
        query_metadata = []

        async with IGVFCatalogClient() as client:
            for endpoint_key in endpoint_keys:
                edge_config = get_edge_config(endpoint_key)
                if not edge_config:
                    continue

                # Determine the correct parameter name for this endpoint
                # The IDParser gives us a generic param_name, but each endpoint may expect different names
                endpoint_param_name = param_name
                if 'from_params' in edge_config:
                    # Check if our param_name is in the allowed list, otherwise use the first one
                    if param_name not in edge_config['from_params']:
                        # Map common parameter names to endpoint-specific ones
                        param_mapping = {
                            'gene_name': 'gene_name',
                            'gene_id': 'gene_id',
                            'protein_id': 'protein_id',
                            'variant_id': 'variant_id',
                            'rsid': 'rsid',
                            'spdi': 'spdi',
                            'hgvs': 'hgvs',
                            'ca_id': 'ca_id',
                        }
                        endpoint_param_name = param_mapping.get(
                            param_name, edge_config['from_params'][0])

                # Build query parameters
                try:
                    params = build_query_params(
                        normalized_id, endpoint_param_name, edge_config, filters, limit, verbose
                    )

                    # Query the endpoint
                    associations = await client.find_associations(
                        endpoint=edge_config['path'], params=params, verbose=verbose
                    )

                    # Add metadata to each association
                    for assoc in associations:
                        assoc['_endpoint'] = endpoint_key
                        assoc['_endpoint_path'] = edge_config['path']

                    all_associations.extend(associations)

                    query_metadata.append(
                        {
                            'endpoint': endpoint_key,
                            'path': edge_config['path'],
                            'results_count': len(associations),
                            'params_used': {k: v for k, v in params.items() if k not in ['page']},
                        }
                    )

                except Exception as e:
                    # Log error but continue with other endpoints
                    query_metadata.append(
                        {
                            'endpoint': endpoint_key,
                            'path': edge_config['path'],
                            'error': str(e),
                        }
                    )

        # Format response
        response_data = {
            'entity_id': normalized_id,
            'entity_type': entity_type,
            'relationship_type': relationship,
            'num_associations': len(all_associations),
            'query_metadata': query_metadata,
            'associations': all_associations[:limit],  # Respect overall limit
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
