"""Resolve ID tool - convert between identifier formats."""

import json
from typing import Any

from mcp.types import Tool, TextContent

from ..services.api_client import IGVFCatalogClient
from ..services.id_parser import IDParser
from ..services.formatter import format_error


# Tool definition
RESOLVE_ID_TOOL = Tool(
    name='resolve_id',
    description=(
        'Convert between different identifier formats and find all known aliases. '
        'Particularly useful for variants: converts between rsID, SPDI, HGVS, and ClinGen Allele Registry ID. '
        'Also works for genes (get all synonyms), proteins (UniProt, Ensembl), and other entities. '
        'Returns all known identifiers for the entity.'
    ),
    inputSchema={
        'type': 'object',
        'properties': {
            'id': {
                'type': 'string',
                'description': "Identifier to resolve (e.g., 'rs80357906', 'BRCA1', 'NC_000017.11:43044295:G:A')",
            },
            'target_type': {
                'type': 'string',
                'description': 'Preferred output format (optional)',
            },
        },
        'required': ['id'],
    },
)


async def resolve_id(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute the resolve_id tool.

    Args:
        arguments: Tool arguments with 'id' and optional 'target_type'

    Returns:
        List of TextContent with all identifiers for the entity
    """
    try:
        entity_id = arguments['id']
        target_type = arguments.get('target_type')

        # Detect entity type
        entity_type, param_name = IDParser.detect_entity_type(entity_id)
        normalized_id = IDParser.normalize_identifier(entity_id, entity_type)

        # Query the API to get the full entity
        async with IGVFCatalogClient() as client:
            entities = await client.get_entity(
                entity_type=entity_type,
                param_name=param_name,
                param_value=normalized_id,
            )

        if not entities:
            return [
                TextContent(
                    type='text',
                    text=f"No {entity_type} found with {param_name}='{normalized_id}'",
                )
            ]

        entity = entities[0]

        # Extract identifiers based on entity type
        identifiers = {'input': entity_id, 'entity_type': entity_type}

        if entity_type == 'variant':
            # Variant identifiers
            identifiers['identifiers'] = {
                'rsid': entity.get('rsid'),
                'spdi': entity.get('spdi'),
                'hgvs': entity.get('hgvs'),
                'ca_id': entity.get('ca_id'),
                'variant_id': entity.get('_id'),
                'chromosome': entity.get('chr'),
                'position': entity.get('pos'),
                'ref': entity.get('ref'),
                'alt': entity.get('alt'),
            }
        elif entity_type == 'gene':
            # Gene identifiers
            identifiers['identifiers'] = {
                'gene_id': entity.get('_id'),
                'name': entity.get('name'),
                'hgnc': entity.get('hgnc'),
                'entrez': entity.get('entrez'),
                'synonyms': entity.get('synonyms', []),
                'chromosome': entity.get('chr'),
                'start': entity.get('start'),
                'end': entity.get('end'),
            }
        elif entity_type == 'protein':
            # Protein identifiers
            identifiers['identifiers'] = {
                'protein_id': entity.get('_id'),
                'names': entity.get('names', []),
                'dbxrefs': entity.get('dbxrefs', []),
                'full_name': entity.get('full_name'),
            }
        elif entity_type == 'transcript':
            # Transcript identifiers
            identifiers['identifiers'] = {
                'transcript_id': entity.get('_id'),
                'chromosome': entity.get('chr'),
                'start': entity.get('start'),
                'end': entity.get('end'),
                'transcript_type': entity.get('transcript_type'),
            }
        elif entity_type == 'ontology':
            # Ontology term identifiers
            identifiers['identifiers'] = {
                'term_id': entity.get('_id'),
                'name': entity.get('name'),
                'synonyms': entity.get('synonyms', []),
                'source': entity.get('source'),
            }
        else:
            # Generic identifiers
            identifiers['identifiers'] = {
                'id': entity.get('_id'),
                'name': entity.get('name'),
            }

        # Remove None values
        if 'identifiers' in identifiers:
            identifiers['identifiers'] = {
                k: v for k, v in identifiers['identifiers'].items() if v is not None
            }

        response_text = json.dumps(identifiers, indent=2)

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
                text=f'Error resolving identifier: {format_error(e)}',
            )
        ]
