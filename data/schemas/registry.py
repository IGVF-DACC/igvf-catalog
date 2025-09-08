import json
import os
import jsonref
from jsonschema import Draft202012Validator

# Load the registry from JSON file


def load_registry():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    registry_path = os.path.join(current_dir, 'registry.json')

    with open(registry_path, 'r') as f:
        return json.load(f)


# Export the registry
registry = load_registry()


def merge_allof_schema(schema):
    """Merge allOf schemas into a single schema"""
    if not isinstance(schema, dict) or 'allOf' not in schema:
        return schema

    # Start with the first schema in allOf
    merged = schema['allOf'][0].copy()

    # Merge each subsequent schema
    for schema_item in schema['allOf'][1:]:
        if 'properties' in schema_item and 'properties' in merged:
            merged['properties'].update(schema_item['properties'])
        if 'required' in schema_item and 'required' in merged:
            merged['required'] = list(
                set(merged['required'] + schema_item['required']))
        # Override other properties
        for key, value in schema_item.items():
            if key not in ['properties', 'required']:
                merged[key] = value

    # Remove allOf and add other top-level properties
    result = {k: v for k, v in schema.items() if k != 'allOf'}
    result.update(merged)

    return result


def get_schema(collection_type, collection_name, adapter_name):
    schema_file = registry[collection_type][collection_name][adapter_name]
    current_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(current_dir, '..', schema_file)

    # Load the main schema
    with open(schema_path, 'r') as f:
        schema = json.load(f)

    # Use jsonref to resolve $ref references
    # jsonref automatically handles file:// URIs and relative paths
    base_uri = f'file://{os.path.dirname(schema_path)}/'
    resolved_schema = jsonref.replace_refs(schema, base_uri=base_uri)

    # Merge allOf if present
    final_schema = merge_allof_schema(resolved_schema)

    return final_schema
