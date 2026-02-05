"""Get entity tool - universal entity lookup with auto-detection."""

from typing import Any, Optional

from mcp.types import Tool, TextContent

from ..services.api_client import IGVFCatalogClient
from ..services.id_parser import IDParser
from ..services.formatter import add_entity_type, format_error


# Tool definition
GET_ENTITY_TOOL = Tool(
    name='get_entity',
    description=(
        'Look up any biological entity by ID with automatic type detection. '
        'Supports genes (BRCA1, ENSG00000139618), variants (rs12345, NC_000017.11:43044295:G:A), '
        'proteins (ENSP00000493376, P49711), transcripts (ENST00000443707), '
        'diseases (Orphanet_586, MONDO_0008199), drugs (PA448497), '
        'complexes (CPX-9), and more. '
        'Returns detailed information about the entity.'
    ),
    inputSchema={
        'type': 'object',
        'properties': {
            'id': {
                'type': 'string',
                'description': "Entity identifier (e.g., 'BRCA1', 'rs12345', 'ENSG00000139618')",
            },
            'hint': {
                'type': 'string',
                'description': 'Optional hint about entity type (gene, variant, protein, etc.)',
                'enum': ['gene', 'variant', 'protein', 'transcript', 'disease', 'drug', 'complex'],
            },
        },
        'required': ['id'],
    },
)


async def get_entity(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute the get_entity tool.

    Args:
        arguments: Tool arguments with 'id' and optional 'hint'

    Returns:
        List of TextContent with entity information or error message
    """
    try:
        entity_id = arguments['id']
        hint = arguments.get('hint')

        # Detect entity type
        entity_type, param_name = IDParser.detect_entity_type(entity_id, hint)

        # Normalize the identifier
        normalized_id = IDParser.normalize_identifier(entity_id, entity_type)

        # Query the API
        async with IGVFCatalogClient() as client:
            entities = await client.get_entity(
                entity_type=entity_type,
                param_name=param_name,
                param_value=normalized_id,
            )

        # Format response
        if not entities:
            return [
                TextContent(
                    type='text',
                    text=f"No {entity_type} found with {param_name}='{normalized_id}'",
                )
            ]

        # Add entity type to results
        results = [add_entity_type(entity, entity_type) for entity in entities]

        # Format as JSON
        import json
        response_text = json.dumps(results, indent=2)

        return [
            TextContent(
                type='text',
                text=response_text,
            )
        ]

    except ValueError as e:
        # ID parsing or validation errors
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
                text=f'Error retrieving entity: {format_error(e)}',
            )
        ]
