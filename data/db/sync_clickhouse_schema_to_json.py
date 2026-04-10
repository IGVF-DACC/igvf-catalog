#!/usr/bin/env python3
"""
Generate ClickHouse CREATE TABLE .sql files from JSON Schema definitions.

Reads the schema registry and produces one .sql file per collection,
translating JSON Schema types to ClickHouse column types.

Usage (from the data/ directory):
    python db/sync_clickhouse_schema_to_json.py --output-dir db/schema/collections

Or from anywhere:
    python /path/to/sync_clickhouse_schema_to_json.py --output-dir /tmp/schemas
"""

import argparse
import os
import sys

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if DATA_DIR not in sys.path:
    sys.path.insert(0, DATA_DIR)

from schemas.registry import get_schema, load_registry  # noqa: E402


CLICKHOUSE_RESERVED_WORDS = frozenset([
    'format',
])


def json_type_to_clickhouse(prop_def):
    """Map a JSON Schema property definition to a ClickHouse type string."""
    type_spec = prop_def.get('type')

    if type_spec is None:
        if 'enum' in prop_def:
            return 'String'
        return 'String'

    # Nullable union types like ["string", "null"]
    if isinstance(type_spec, list):
        non_null = [t for t in type_spec if t != 'null']
        if not non_null:
            return 'String'
        base = _simple_type(non_null[0], prop_def)
        if base.startswith('Array('):
            return base
        return f'Nullable({base})'

    return _simple_type(type_spec, prop_def)


def _simple_type(type_name, prop_def):
    """Resolve a single JSON Schema type name to ClickHouse."""
    if type_name == 'string':
        return 'String'
    if type_name == 'number':
        return 'Float64'
    if type_name == 'integer':
        return 'Int64'
    if type_name == 'boolean':
        return 'Bool'
    if type_name == 'array':
        return _array_type(prop_def)
    if type_name == 'object':
        return 'JSON'
    return 'String'


def _array_type(prop_def):
    """Determine the ClickHouse Array element type from items schema."""
    items = prop_def.get('items')
    if items is None:
        return 'Array(String)'
    item_type = items.get('type') if isinstance(items, dict) else None
    if item_type == 'object':
        return 'Array(JSON)'
    if item_type == 'integer':
        return 'Array(Int64)'
    if item_type == 'number':
        return 'Array(Float64)'
    return 'Array(String)'


def escape_column_name(name):
    if name.lower() in CLICKHOUSE_RESERVED_WORDS:
        return name + '_'
    return name


def collect_properties(registry, collection_type, collection_name):
    """
    Union all adapter schemas for a collection into a single properties dict.

    Returns (merged_properties, relationship_ids) where relationship_ids is
    a list of column name strings (only for edges, empty for nodes).
    """
    merged_props = {}
    from_collections = set()
    to_collections = set()

    for adapter_name in registry[collection_type][collection_name]:
        schema = get_schema(collection_type, collection_name, adapter_name)
        props = schema.get('properties', {})

        for prop_name, prop_def in props.items():
            if prop_name in ('_from', '_to'):
                if 'collections' in prop_def:
                    target = from_collections if prop_name == '_from' else to_collections
                    target.update(prop_def['collections'])
                continue
            if prop_name == '_key':
                continue
            if prop_name not in merged_props:
                merged_props[prop_name] = prop_def
            else:
                if isinstance(merged_props[prop_name], dict) and isinstance(prop_def, dict):
                    merged_props[prop_name] = {
                        **merged_props[prop_name], **prop_def}
                else:
                    merged_props[prop_name] = prop_def

    relationship_ids = _build_relationship_ids(
        from_collections, to_collections)
    return merged_props, relationship_ids


def _build_relationship_ids(from_collections, to_collections):
    """
    Translate _from/_to collection sets into ClickHouse column names.

    Self-referencing edges (same collection in both from and to) get
    _1_id / _2_id suffixes; otherwise plain _id.
    """
    if not from_collections and not to_collections:
        return []

    columns = []
    for coll in sorted(from_collections):
        if coll in to_collections:
            columns.append(f'{coll}_1_id')
        else:
            columns.append(f'{coll}_id')
    for coll in sorted(to_collections):
        if coll in from_collections:
            columns.append(f'{coll}_2_id')
        else:
            columns.append(f'{coll}_id')
    return columns


def generate_create_table(collection_name, properties, relationship_ids):
    """Build a CREATE TABLE IF NOT EXISTS SQL statement."""
    lines = []

    for prop_name, prop_def in properties.items():
        col_name = escape_column_name(prop_name)
        ch_type = json_type_to_clickhouse(prop_def)
        lines.append(f'\t{col_name} {ch_type}')

    lines.append('\tid String PRIMARY KEY')

    for rel_col in relationship_ids:
        lines.append(f'\t{rel_col} String')

    columns_sql = ',\n'.join(lines)
    return (
        f'CREATE TABLE IF NOT EXISTS {collection_name} (\n'
        f'{columns_sql}\n'
        f');\n'
    )


def main():
    parser = argparse.ArgumentParser(
        description='Generate ClickHouse CREATE TABLE .sql files from JSON schemas.'
    )
    parser.add_argument(
        '--output-dir',
        required=True,
        help='Directory to write .sql files into (created if missing).',
    )
    parser.add_argument(
        '--collection',
        default=None,
        help='Generate only for a specific collection name.',
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    registry = load_registry()
    generated = []

    for collection_type in ('nodes', 'edges'):
        for collection_name in registry[collection_type]:
            if args.collection and collection_name != args.collection:
                continue

            props, rel_ids = collect_properties(
                registry, collection_type, collection_name
            )
            sql = generate_create_table(collection_name, props, rel_ids)

            out_path = os.path.join(args.output_dir, f'{collection_name}.sql')
            with open(out_path, 'w') as f:
                f.write(sql)

            generated.append(collection_name)

    print(f'Generated {len(generated)} SQL files in {args.output_dir}/')
    for name in generated:
        print(f'  {name}.sql')


if __name__ == '__main__':
    main()
