"""Response formatting utilities."""

from typing import Any


def add_entity_type(entity: dict[str, Any], entity_type: str) -> dict[str, Any]:
    """
    Add _type field to an entity object.

    Args:
        entity: Entity dictionary
        entity_type: Type of entity

    Returns:
        Entity with _type field added
    """
    return {'_type': entity_type, **entity}


def format_error(error: Exception) -> str:
    """
    Format an error message in a user-friendly way.

    Args:
        error: Exception to format

    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_msg = str(error)

    # Add helpful context for common errors
    if 'Invalid region format' in error_msg:
        return f'{error_msg}\n\nExamples:\n- chr1:1000-2000\n- 1:1M-2M\n- chrX:1000000-2000000'

    if 'Could not detect entity type' in error_msg:
        return error_msg

    return f'{error_type}: {error_msg}'
