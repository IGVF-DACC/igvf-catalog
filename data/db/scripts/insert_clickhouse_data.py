#!/usr/bin/env python3
"""
Load ClickHouse table data from a directory of import-statement YAMLs.

Each YAML file in ``<insert-dir>`` has the form

    <table>: |
      INSERT INTO <table> (...)
        SELECT ... FROM s3('...', 'JSONEachRow', '...');

Iterates in alphabetical order. For each table:

  * If the table doesn't exist → fail (run ``create_clickhouse_tables.py`` first).
  * If the table is empty → run the INSERT.
  * If the table is populated:
      - without ``--reload`` → skip with a warning.
      - with ``--reload``    → TRUNCATE (using ``max_table_size_to_drop = 0``)
                                then INSERT.

A YAML body may contain multiple ``;``-separated statements (e.g. a hand-
crafted symmetrized load that does two INSERTs); all of them run sequentially.

Examples:
  # Load everything missing from S3
  ./insert_clickhouse_data.py \
      --insert-dir data/db/generated_import_statements \
      --host 35.85.61.200

  # Reload a single table (TRUNCATE + INSERT)
  ./insert_clickhouse_data.py \
      --insert-dir data/db/generated_import_statements \
      --host 35.85.61.200 --reload --only drugs
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------

def http_query(url: str, db: str, user: str, password: str, sql: str,
               timeout: float | None = None) -> str:
    full = f'{url}/?{urllib.parse.urlencode({"database": db})}'
    req = urllib.request.Request(
        full,
        data=sql.encode('utf-8'),
        method='POST',
        headers={'X-ClickHouse-User': user, 'X-ClickHouse-Key': password},
    )
    if timeout is None:
        # urllib's "no timeout" is omitting the keyword, not passing None.
        with urllib.request.urlopen(req) as r:
            return r.read().decode('utf-8')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8')


# ---------------------------------------------------------------------------
# YAML parser (single-key mapping with literal block scalar)
# ---------------------------------------------------------------------------

_YAML_HEADER_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*\|')


def parse_yaml(yaml_text: str, fallback_table: str) -> tuple[str, str]:
    """Parse a `<name>: |` literal-block YAML and return (table, sql).

    Falls back to ``fallback_table`` if the header line is missing.
    """
    lines = yaml_text.splitlines()
    if not lines:
        return fallback_table, ''

    m = _YAML_HEADER_RE.match(lines[0])
    if not m:
        # Not a YAML mapping — treat the whole file as raw SQL.
        return fallback_table, yaml_text.strip()

    table = m.group(1)
    # Strip 2-space indent on continuation lines; tolerate blank lines.
    body_lines: list[str] = []
    for line in lines[1:]:
        if line.startswith('  '):
            body_lines.append(line[2:])
        elif line.strip() == '':
            body_lines.append('')
        else:
            break
    return table, '\n'.join(body_lines).strip()


# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------

_COMMENT_RE = re.compile(r'--.*$', re.MULTILINE)


def split_statements(sql_text: str) -> list[str]:
    """Strip line comments and split on ``;``."""
    cleaned = _COMMENT_RE.sub('', sql_text)
    return [s.strip() for s in cleaned.split(';') if s.strip()]


def table_exists(url: str, db: str, user: str, password: str, table: str) -> bool:
    sql = (
        'SELECT count() FROM system.tables '
        'WHERE database = {db:String} AND name = {tbl:String}'
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


def count_rows(url: str, db: str, user: str, password: str, table: str) -> int:
    out = http_query(url, db, user, password,
                     f'SELECT count() FROM {table}', timeout=60)
    return int(out.strip())


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
    INSERTED = 'inserted'
    RELOADED = 'reloaded'
    POPULATED = 'populated'   # skipped because non-empty and no --reload
    MISSING = 'missing'        # table doesn't exist
    FAILED = 'failed'
    SKIPPED = 'skipped'        # filtered or empty file


def fmt_rows(n: int) -> str:
    return f'{n:,} rows'


def fmt_elapsed(secs: float) -> str:
    if secs < 60:
        return f'{secs:.1f}s'
    m, s = divmod(secs, 60)
    if m < 60:
        return f'{int(m)}m{int(s)}s'
    h, m = divmod(m, 60)
    return f'{int(h)}h{int(m)}m'


def process_file(yaml_file: Path, url: str, db: str, user: str, password: str,
                 reload: bool, dry_run: bool) -> tuple[str, str]:
    """Returns (status, detail)."""
    raw = yaml_file.read_text()
    table, sql_body = parse_yaml(raw, fallback_table=yaml_file.stem)
    statements = split_statements(sql_body)

    if not statements:
        return Result.SKIPPED, 'no statements'

    if dry_run:
        action = 'reload' if reload else 'load'
        return Result.SKIPPED, f'would {action} ({len(statements)} statement(s)) into {table}'

    if not table_exists(url, db, user, password, table):
        return Result.MISSING, (
            f'table {table!r} does not exist; '
            f'run create_clickhouse_tables.py first'
        )

    rows_before = count_rows(url, db, user, password, table)

    if rows_before > 0 and not reload:
        return Result.POPULATED, f'{fmt_rows(rows_before)}; pass --reload to wipe & reinsert'

    if rows_before > 0 and reload:
        http_query(
            url, db, user, password,
            f'TRUNCATE TABLE {table} SETTINGS max_table_size_to_drop = 0',
            timeout=120,
        )

    t0 = time.perf_counter()
    for stmt in statements:
        # No client timeout — large INSERT FROM s3 can take many minutes.
        http_query(url, db, user, password, stmt, timeout=None)
    elapsed = time.perf_counter() - t0

    rows_after = count_rows(url, db, user, password, table)
    status = Result.RELOADED if rows_before > 0 else Result.INSERTED
    return status, f'{fmt_rows(rows_after)} in {fmt_elapsed(elapsed)}'


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(
        description='Load ClickHouse table data from a directory of import-statement YAMLs.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument('--insert-dir', required=True,
                   help='Directory containing import-statement *.yaml files.')
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
                   help='Only process tables matching this glob (repeatable).')
    p.add_argument('--exclude', action='append', default=[], metavar='PATTERN',
                   help='Skip tables matching this glob (repeatable).')
    p.add_argument('--reload', action='store_true',
                   help='TRUNCATE populated tables before INSERT '
                        '(uses max_table_size_to_drop = 0).')
    p.add_argument('--fail-fast', action='store_true',
                   help='Stop on first failure instead of continuing.')
    p.add_argument('--dry-run', action='store_true',
                   help='Print what would be done; do not connect to ClickHouse.')
    args = p.parse_args()

    password = args.password or os.environ.get('CLICKHOUSE_PASSWORD')
    if not password and not args.dry_run:
        print('ERROR: password is required. Pass --password or set the '
              'CLICKHOUSE_PASSWORD env var.', file=sys.stderr)
        return 2

    insert_dir = Path(args.insert_dir).resolve()
    if not insert_dir.is_dir():
        print(f'ERROR: {insert_dir} is not a directory', file=sys.stderr)
        return 2

    yaml_files = sorted(insert_dir.glob('*.yaml'))
    if not yaml_files:
        print(f'ERROR: no .yaml files found in {insert_dir}', file=sys.stderr)
        return 2

    url = f'http://{args.host}:{args.port}'

    print(f'{"DRY-RUN: " if args.dry_run else ""}'
          f'{len(yaml_files)} .yaml files in '
          f'{insert_dir.relative_to(Path.cwd()) if insert_dir.is_relative_to(Path.cwd()) else insert_dir}'
          f' -> {url} (db={args.database})',
          file=sys.stderr)

    counts: dict[str, int] = {}
    failures: list[tuple[str, str]] = []

    for yaml_file in yaml_files:
        table_guess = yaml_file.stem
        if not matches_filters(table_guess, args.only, args.exclude):
            continue

        # Print a "running" line up front so long INSERTs (minutes) aren't
        # silent. Use stderr so stdout stays clean for the status lines.
        if not args.dry_run:
            print(f'  {"running":10s} {table_guess}',
                  file=sys.stderr, flush=True)

        try:
            status, detail = process_file(
                yaml_file, url, args.database, args.user, password or '',
                reload=args.reload, dry_run=args.dry_run,
            )
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='replace').strip()
            first_line = err_body.splitlines(
            )[0] if err_body else f'HTTP {e.code}'
            failures.append((table_guess, first_line[:300]))
            counts[Result.FAILED] = counts.get(Result.FAILED, 0) + 1
            print(f'  {Result.FAILED:10s} {table_guess:40s} {first_line[:120]}',
                  file=sys.stderr)
            if args.fail_fast:
                break
            continue
        except Exception as e:
            failures.append((table_guess, str(e)[:300]))
            counts[Result.FAILED] = counts.get(Result.FAILED, 0) + 1
            print(f'  {Result.FAILED:10s} {table_guess:40s} {str(e)[:120]}',
                  file=sys.stderr)
            if args.fail_fast:
                break
            continue

        counts[status] = counts.get(status, 0) + 1
        if status == Result.MISSING:
            failures.append((table_guess, detail))
        suffix = f' ({detail})' if detail else ''
        print(f'  {status:10s} {table_guess:40s}{suffix}')

    print()
    print('Summary:')
    for status in (Result.INSERTED, Result.RELOADED, Result.POPULATED,
                   Result.MISSING, Result.SKIPPED, Result.FAILED):
        n = counts.get(status, 0)
        if n > 0:
            print(f'  {status:10s} {n}')

    if failures:
        print()
        print('Failures / missing:')
        for t, e in failures:
            print(f'  {t}: {e}')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
