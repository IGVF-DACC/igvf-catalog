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
    """
    Merge allOf schemas into a single schema.

    Since we use a flattened allOf structure (no nested allOf),
    this merges all schemas in the allOf array sequentially.

    For properties: Child definitions are MERGED with base definitions,
    not replaced. This means:
    - Base defines: {type, description}
    - Child adds: {enum, pattern, example}
    - Result: {type, description, enum, pattern, example}
    """
    if not isinstance(schema, dict) or 'allOf' not in schema:
        return schema

    # Start with an empty merged schema
    merged = {}

    # Merge each schema in allOf sequentially
    for schema_item in schema['allOf']:
        # Merge properties (deep merge for each property)
        if 'properties' in schema_item:
            if 'properties' not in merged:
                merged['properties'] = {}

            for prop_name, prop_value in schema_item['properties'].items():
                if prop_name not in merged['properties']:
                    # New property, add it directly
                    merged['properties'][prop_name] = prop_value.copy(
                    ) if isinstance(prop_value, dict) else prop_value
                else:
                    # Property exists, merge the definitions
                    existing_prop = merged['properties'][prop_name]
                    if isinstance(existing_prop, dict) and isinstance(prop_value, dict):
                        # Deep merge: child's values override/extend base's values
                        merged['properties'][prop_name] = {
                            **existing_prop, **prop_value}
                    else:
                        # Not a dict, just replace
                        merged['properties'][prop_name] = prop_value

        # Merge required (combine and deduplicate)
        if 'required' in schema_item:
            if 'required' not in merged:
                merged['required'] = []
            merged['required'] = list(
                set(merged['required'] + schema_item['required']))

        # Copy or override other properties
        # Note: Later items override earlier items for non-mergeable properties
        for key, value in schema_item.items():
            if key not in ['properties', 'required']:
                merged[key] = value

    # Add top-level properties from the original schema (except allOf)
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
