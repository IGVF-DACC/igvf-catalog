#!/usr/bin/env python3
"""
Create (or recreate) ClickHouse tables from a directory of .sql files.

Iterates ``<schema-dir>/*.sql`` in alphabetical order. Each file is sent
verbatim to the ClickHouse HTTP endpoint, after splitting on ``;`` so multi-
statement DDL bundles (e.g. ``ALTER TABLE … ADD INDEX …;`` chains) work too.

Idempotent by default — ``CREATE TABLE IF NOT EXISTS`` is a no-op for existing
tables, and the script reports that explicitly. Pass ``--recreate`` to drop
the table first (using ``max_table_size_to_drop = 0`` so big tables can be
dropped without server-side reconfiguration).

Examples:
  # Create every missing table from the generated schemas
  ./create_clickhouse_tables.py \
      --schema-dir data/db/generated_schemas \
      --host 35.85.61.200

  # Recreate just two tables (drops first, then CREATEs)
  ./create_clickhouse_tables.py \
      --schema-dir data/db/generated_schemas \
      --host 35.85.61.200 --recreate \
      --only drugs --only complexes

  # Apply an index DDL bundle
  ./create_clickhouse_tables.py \
      --schema-dir data/db --host 35.85.61.200 --only genes_indexes
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------

def http_query(url: str, db: str, user: str, password: str, sql: str) -> str:
    full = f'{url}/?{urllib.parse.urlencode({"database": db})}'
    req = urllib.request.Request(
        full,
        data=sql.encode('utf-8'),
        method='POST',
        headers={'X-ClickHouse-User': user, 'X-ClickHouse-Key': password},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read().decode('utf-8')


# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------

_COMMENT_RE = re.compile(r'--.*$', re.MULTILINE)
_CREATE_TABLE_RE = re.compile(r'^\s*CREATE\s+TABLE\b', re.IGNORECASE)


def split_statements(sql_text: str) -> list[str]:
    """Split a multi-statement SQL into a list of individual statements.

    Removes line comments (``-- ...``) and splits on ``;``. We don't have
    string-literal semicolons in any of our DDL, so a naive split is safe.
    """
    cleaned = _COMMENT_RE.sub('', sql_text)
    return [s.strip() for s in cleaned.split(';') if s.strip()]


def is_single_create_table(statements: list[str]) -> bool:
    return len(statements) == 1 and bool(_CREATE_TABLE_RE.match(statements[0]))


def table_exists(url: str, db: str, user: str, password: str, table: str) -> bool:
    # Use parameterized query to be safe even with weird table names.
    sql = (
        'SELECT count() FROM system.tables '
        f'WHERE database = {{db:String}} AND name = {{tbl:String}}'
    )
    qs = urllib.parse.urlencode({
        'database': db,
        'param_db': db,
        'param_tbl': table,
    })
    full = f'{url}/?{qs}'
    req = urllib.request.Request(
        full,
        data=sql.encode('utf-8'),
        method='POST',
        headers={'X-ClickHouse-User': user, 'X-ClickHouse-Key': password},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return int(r.read().decode().strip()) > 0


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def matches_filters(table: str, only: list[str], exclude: list[str]) -> bool:
    if only and not any(fnmatch.fnmatch(table, pat) for pat in only):
        return False
    if any(fnmatch.fnmatch(table, pat) for pat in exclude):
        return False
    return True


# ---------------------------------------------------------------------------
# Per-file processing
# ---------------------------------------------------------------------------

class Result:
    CREATED = 'created'
    RECREATED = 'recreated'
    EXISTS = 'exists'
    APPLIED = 'applied'   # multi-statement DDL bundle
    FAILED = 'failed'
    SKIPPED = 'skipped'   # filtered out or empty


def process_file(sql_file: Path, url: str, db: str, user: str, password: str,
                 recreate: bool, dry_run: bool) -> tuple[str, str]:
    """Returns (status, detail). status is one of Result.*."""
    table = sql_file.stem
    body = sql_file.read_text()
    statements = split_statements(body)

    if not statements:
        return Result.SKIPPED, 'empty after stripping comments'

    single = is_single_create_table(statements)

    if dry_run:
        if single:
            return Result.SKIPPED, f'would {"recreate" if recreate else "create"} (1 statement)'
        return Result.SKIPPED, f'would apply {len(statements)} statement(s)'

    if single:
        existed = table_exists(url, db, user, password, table)
        if existed and not recreate:
            return Result.EXISTS, ''
        if existed and recreate:
            http_query(
                url, db, user, password,
                f'DROP TABLE IF EXISTS {table} SETTINGS max_table_size_to_drop = 0',
            )
        http_query(url, db, user, password, statements[0])
        return (Result.RECREATED if (existed and recreate) else Result.CREATED), ''

    # Multi-statement bundle (e.g. ALTER / MATERIALIZE chains).
    for stmt in statements:
        http_query(url, db, user, password, stmt)
    return Result.APPLIED, f'{len(statements)} statement(s)'


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(
        description='Create or recreate ClickHouse tables from .sql files in a directory.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument('--schema-dir', required=True,
                   help='Directory containing .sql files. Each file is run as a CREATE TABLE '
                        '(or multi-statement DDL bundle).')
    p.add_argument('--host', required=True,
                   help='ClickHouse host (IP or hostname).')
    p.add_argument('--port', default=8123, type=int,
                   help='ClickHouse HTTP port (default: 8123).')
    p.add_argument('--database', default='igvf',
                   help='Database name (default: igvf).')
    p.add_argument('--user', default='default',
                   help='ClickHouse user (default: default).')
    p.add_argument('--password', default=None,
                   help='ClickHouse password. If omitted, reads CLICKHOUSE_PASSWORD env var; '
                        'errors if neither is set.')
    p.add_argument('--only', action='append', default=[], metavar='PATTERN',
                   help='Only process tables matching this glob (repeatable). '
                        'E.g. --only drugs --only complex_*.')
    p.add_argument('--exclude', action='append', default=[], metavar='PATTERN',
                   help='Skip tables matching this glob (repeatable).')
    p.add_argument('--recreate', action='store_true',
                   help='DROP TABLE IF EXISTS before CREATE (overrides max_table_size_to_drop). '
                        'Only meaningful for single-statement CREATE TABLE files.')
    p.add_argument('--fail-fast', action='store_true',
                   help='Stop on first failure instead of continuing.')
    p.add_argument('--dry-run', action='store_true',
                   help='Print what would be done; do not connect to ClickHouse.')
    args = p.parse_args()

    # Resolve password.
    password = args.password or os.environ.get('CLICKHOUSE_PASSWORD')
    if not password and not args.dry_run:
        print('ERROR: password is required. Pass --password or set the '
              'CLICKHOUSE_PASSWORD env var.', file=sys.stderr)
        return 2

    schema_dir = Path(args.schema_dir).resolve()
    if not schema_dir.is_dir():
        print(f'ERROR: {schema_dir} is not a directory', file=sys.stderr)
        return 2

    sql_files = sorted(schema_dir.glob('*.sql'))
    if not sql_files:
        print(f'ERROR: no .sql files found in {schema_dir}', file=sys.stderr)
        return 2

    url = f'http://{args.host}:{args.port}'

    print(f'{"DRY-RUN: " if args.dry_run else ""}'
          f'{len(sql_files)} .sql files in {schema_dir.relative_to(Path.cwd()) if schema_dir.is_relative_to(Path.cwd()) else schema_dir}'
          f' -> {url} (db={args.database})',
          file=sys.stderr)

    counts: dict[str, int] = {}
    failures: list[tuple[str, str]] = []

    for sql_file in sql_files:
        table = sql_file.stem
        if not matches_filters(table, args.only, args.exclude):
            continue

        try:
            status, detail = process_file(
                sql_file, url, args.database, args.user, password or '',
                recreate=args.recreate, dry_run=args.dry_run,
            )
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='replace').strip()
            first_line = err_body.splitlines(
            )[0] if err_body else f'HTTP {e.code}'
            failures.append((table, first_line[:300]))
            counts[Result.FAILED] = counts.get(Result.FAILED, 0) + 1
            print(f'  {Result.FAILED:10s} {table:40s} {first_line[:120]}',
                  file=sys.stderr)
            if args.fail_fast:
                break
            continue
        except Exception as e:  # network errors, etc.
            failures.append((table, str(e)[:300]))
            counts[Result.FAILED] = counts.get(Result.FAILED, 0) + 1
            print(f'  {Result.FAILED:10s} {table:40s} {str(e)[:120]}',
                  file=sys.stderr)
            if args.fail_fast:
                break
            continue

        counts[status] = counts.get(status, 0) + 1
        suffix = f' ({detail})' if detail else ''
        print(f'  {status:10s} {table:40s}{suffix}')

    # Summary.
    print()
    print('Summary:')
    for status in (Result.CREATED, Result.RECREATED, Result.EXISTS,
                   Result.APPLIED, Result.SKIPPED, Result.FAILED):
        n = counts.get(status, 0)
        if n > 0:
            print(f'  {status:10s} {n}')
    if failures:
        print()
        print('Failures:')
        for t, e in failures:
            print(f'  {t}: {e}')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
