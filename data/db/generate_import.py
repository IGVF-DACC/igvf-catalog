#!/usr/bin/env python3
"""Generate a ClickHouse S3 import YAML statement from a CREATE TABLE SQL schema."""

import argparse
import re
import sys


def parse_sql_schema(sql_text: str) -> list[tuple[str, str, bool]]:
    """Parse CREATE TABLE SQL and return [(col_name, col_type, is_primary_key), ...]."""
    body_match = re.search(r'\(\s*\n?(.*)\)', sql_text, re.DOTALL)
    if not body_match:
        print('Error: could not find column definitions in SQL', file=sys.stderr)
        sys.exit(1)

    columns = []
    for line in body_match.group(1).splitlines():
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


def generate_import(schema_path: str, collection: str, s3_path: str) -> str:
    with open(schema_path) as f:
        sql_text = f.read()

    columns = parse_sql_schema(sql_text)

    # FK columns are the _id columns that appear AFTER the PRIMARY KEY id column.
    pk_index = next(
        (i for i, (name, _, is_pk) in enumerate(
            columns) if name == 'id' and is_pk),
        None,
    )
    fk_names = set()
    if pk_index is not None:
        fk_names = {
            name for name, _, _ in columns[pk_index + 1:] if name.endswith('_id')
        }

    insert_cols = []
    select_exprs = []
    s3_fields = []
    fk_count = 0

    for col_name, _col_type, is_pk in columns:
        qname = quote_col(col_name)
        insert_cols.append(qname)

        if is_pk and col_name == 'id':
            select_exprs.append('_key as id')
            s3_fields.append('_key String')
        elif col_name in fk_names:
            fk_count += 1
            arango_field = '_from' if fk_count == 1 else '_to'
            select_exprs.append(
                f"splitByString('/', assumeNotNull({arango_field}))[2] as {qname}"
            )
            s3_fields.append(f'{arango_field} String')
        else:
            select_exprs.append(qname)
            s3_fields.append(f'{qname} {_col_type}')

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
    parser.add_argument('--output', help='Output file path (default: stdout)')
    args = parser.parse_args()

    yaml_output = generate_import(args.schema, args.collection, args.s3_path)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(yaml_output)
    else:
        print(yaml_output, end='')


if __name__ == '__main__':
    main()
