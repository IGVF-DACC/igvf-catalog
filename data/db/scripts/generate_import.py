#!/usr/bin/env python3
"""Generate a ClickHouse S3 import YAML statement from a CREATE TABLE SQL schema.

For edge collections whose Arango ``_from`` and/or ``_to`` references are
polymorphic (e.g. ``_from`` may be a ``proteins/...`` *or* ``transcripts/...``
document, as in ``gene_products_terms``), the ClickHouse schema generator
splits each polymorphic field into one ``<collection>_id`` column per target
collection. This script consults the source JSON Schema(s) under
``data/schemas/{nodes,edges}/<collection>.*.json`` to recover the mapping and
emit the right ``if(startsWith(_from, 'proteins/'), ...)`` routing for each
column.
"""

import argparse
import json
import re
import sys
from pathlib import Path


def parse_sql_schema(sql_text: str) -> list[tuple[str, str, bool]]:
    """Parse CREATE TABLE SQL and return [(col_name, col_type, is_primary_key), ...].

    Reads line-by-line so the column body parser doesn't get confused by
    table-level ``ENGINE = MergeTree ORDER BY (a, b, c)`` clauses, which were
    swallowed by the previous greedy ``\\(.*\\)`` regex.
    """
    lines = sql_text.splitlines()
    in_body = False
    body_lines: list[str] = []
    for raw in lines:
        stripped = raw.strip()
        if not in_body:
            # The opening ( of the column block sits at the end of the
            # `CREATE TABLE ... (` line.
            if stripped.endswith('('):
                in_body = True
            continue
        # The closing ) of the column block is on its own line (possibly
        # followed by ENGINE / ORDER BY / SETTINGS / ;). Inner parens like
        # `LowCardinality(String)` don't appear at the start of a line.
        if stripped.startswith(')'):
            break
        body_lines.append(raw)

    columns: list[tuple[str, str, bool]] = []
    for line in body_lines:
        line = line.strip().rstrip(',')
        if not line:
            continue

        is_pk = 'PRIMARY KEY' in line
        line = line.replace('PRIMARY KEY', '').strip()

        m = re.match(r'^`([^`]+)`\s+(.+)$', line)
        if not m:
            m = re.match(r'^(\S+)\s+(.+)$', line)
        if m:
            columns.append((m.group(1), m.group(2).strip(), is_pk))

    return columns


def quote_col(name: str) -> str:
    """Backtick-quote column names that start with a digit or contain special chars."""
    if re.match(r'^\d', name) or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        return f'`{name}`'
    return name


# ---------------------------------------------------------------------------
# JSON-schema-driven FK origin lookup
# ---------------------------------------------------------------------------

def _find_property(node, name: str):
    """Walk a JSON Schema (handling allOf/oneOf inheritance) to find a property."""
    if isinstance(node, dict):
        props = node.get('properties')
        if isinstance(props, dict) and name in props:
            return props[name]
        for v in node.values():
            found = _find_property(v, name)
            if found is not None:
                return found
    elif isinstance(node, list):
        for x in node:
            found = _find_property(x, name)
            if found is not None:
                return found
    return None


def discover_fk_origins(collection: str, schemas_dir: Path) -> dict[str, tuple[str, str, bool]]:
    """Return ``{column_name: (arango_field, target_collection, is_polymorphic)}``.

    ``arango_field`` is ``'_from'`` or ``'_to'``. ``is_polymorphic`` indicates
    whether the corresponding Arango field can reference more than one
    collection, in which case the import must route by prefix.

    The Arango → ClickHouse schema generator turns ``_from: {collections:
    [proteins, transcripts]}`` into two columns (``proteins_id`` and
    ``transcripts_id``), one populated per row depending on the prefix. We
    recover that mapping by unioning collection sets across every JSON Schema
    declared for the table.
    """
    by_arango_field: dict[str, set[str]] = {'_from': set(), '_to': set()}

    json_paths: list[Path] = []
    for sub in ('nodes', 'edges'):
        json_paths.extend(schemas_dir.joinpath(
            sub).glob(f'{collection}.*.json'))

    for jp in json_paths:
        try:
            schema = json.loads(jp.read_text())
        except Exception:
            continue
        for field in ('_from', '_to'):
            prop = _find_property(schema, field)
            if not isinstance(prop, dict):
                continue
            cols = prop.get('collections', [])
            if isinstance(cols, list):
                by_arango_field[field].update(
                    c for c in cols if isinstance(c, str))

    result: dict[str, tuple[str, str, bool]] = {}
    for arango_field, cols in by_arango_field.items():
        is_poly = len(cols) > 1
        for coll in cols:
            result[f'{coll}_id'] = (arango_field, coll, is_poly)
    return result


# ---------------------------------------------------------------------------
# Import statement generation
# ---------------------------------------------------------------------------

def generate_import(schema_path: str, collection: str, s3_path: str,
                    schemas_dir: Path | None = None) -> str:
    sql_text = Path(schema_path).read_text()
    columns = parse_sql_schema(sql_text)

    if schemas_dir is None:
        # data/db/generate_import.py is two levels deep from data/
        schemas_dir = Path(__file__).resolve().parent.parent / 'schemas'

    fk_origins = discover_fk_origins(collection, schemas_dir)

    # Fall-back FK detection (when no JSON schema is available): treat *_id
    # columns after PRIMARY KEY as edge endpoints, first one == _from.
    pk_index = next(
        (i for i, (name, _, is_pk) in enumerate(
            columns) if name == 'id' and is_pk),
        None,
    )
    fallback_fk_names: list[str] = []
    if pk_index is not None:
        fallback_fk_names = [
            name for name, _, _ in columns[pk_index + 1:] if name.endswith('_id')
        ]

    insert_cols: list[str] = []
    select_exprs: list[str] = []
    s3_fields: list[str] = []
    seen_arango_fields: set[str] = set()
    fallback_seen = 0

    for col_name, col_type, is_pk in columns:
        qname = quote_col(col_name)
        insert_cols.append(qname)

        if is_pk and col_name == 'id':
            select_exprs.append('_key as id')
            s3_fields.append('_key String')
            continue

        # Polymorphic / single FK from JSON schema, when available.
        if col_name in fk_origins:
            arango_field, target_coll, is_poly = fk_origins[col_name]
            if is_poly:
                select_exprs.append(
                    f"splitByString('/', if(startsWith(assumeNotNull({arango_field}), "
                    f"'{target_coll}/'), assumeNotNull({arango_field}), '/'))[2] "
                    f'as {qname}'
                )
            else:
                select_exprs.append(
                    f"splitByString('/', assumeNotNull({arango_field}))[2] as {qname}"
                )
            if arango_field not in seen_arango_fields:
                seen_arango_fields.add(arango_field)
                s3_fields.append(f'{arango_field} String')
            continue

        # Fallback for tables without a JSON schema we could read.
        if col_name in fallback_fk_names:
            fallback_seen += 1
            arango_field = '_from' if fallback_seen == 1 else '_to'
            select_exprs.append(
                f"splitByString('/', assumeNotNull({arango_field}))[2] as {qname}"
            )
            if arango_field not in seen_arango_fields:
                seen_arango_fields.add(arango_field)
                s3_fields.append(f'{arango_field} String')
            continue

        select_exprs.append(qname)
        s3_fields.append(f'{qname} {col_type}')

    insert_list = ', '.join(insert_cols)
    select_list = ', '.join(select_exprs)
    s3_schema = ', '.join(s3_fields)

    stmt = (
        f'INSERT INTO {collection} ({insert_list})\n'
        f'  SELECT {select_list}\n'
        f"  FROM s3('{s3_path}', 'JSONEachRow', '{s3_schema}');"
    )

    return f'{collection}: |\n  {stmt}\n'


def main():
    parser = argparse.ArgumentParser(
        description='Generate a ClickHouse S3 import YAML statement from a CREATE TABLE SQL schema.'
    )
    parser.add_argument(
        '--schema',
        required=True,
        help='Path to .sql file with CREATE TABLE statement',
    )
    parser.add_argument('--collection', required=True,
                        help='Collection/table name')
    parser.add_argument(
        '--s3-path', required=True, help='S3 URL for the s3() function'
    )
    parser.add_argument(
        '--schemas-dir',
        help='Path to the JSON schemas directory (default: data/schemas/ '
             'relative to this script).'
    )
    parser.add_argument('--output', help='Output file path (default: stdout)')
    args = parser.parse_args()

    schemas_dir = Path(args.schemas_dir).resolve(
    ) if args.schemas_dir else None
    yaml_output = generate_import(
        args.schema, args.collection, args.s3_path, schemas_dir=schemas_dir
    )

    if args.output:
        with open(args.output, 'w') as f:
            f.write(yaml_output)
    else:
        print(yaml_output, end='')


if __name__ == '__main__':
    main()
