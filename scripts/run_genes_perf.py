#!/usr/bin/env python3
"""Run genes_perf_tests.sql against the dev ClickHouse and write results to
clickhouserewrite/testing.md.

Reads ClickHouse credentials from <repo>/development.json.dontcommit (same file
the local API uses). No external dependencies — uses urllib only.
"""

from __future__ import annotations

import json
import re
import statistics
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG = REPO_ROOT / 'development.json.dontcommit'
TESTS_FILE = REPO_ROOT / 'data' / 'db' / 'genes_perf_tests.sql'
RESULTS_OUT = REPO_ROOT / 'clickhouserewrite' / 'testing.md'

RESULTS_HEADER = '## Genes table indexing benchmarks'


def load_config() -> tuple[str, str, str, str]:
    cfg = json.loads(CONFIG.read_text())['database']
    return cfg['url'].rstrip('/'), cfg['name'], cfg['username'], cfg['password']


def parse_tests(text: str) -> list[tuple[str, str]]:
    """Split the SQL file into (name, sql) pairs based on `-- TNN_name` markers."""
    tests: list[tuple[str, str]] = []
    name = None
    buf: list[str] = []
    for raw in text.splitlines():
        m = re.match(r'^--\s*(T\d+_[A-Za-z0-9_]+)', raw)
        if m:
            if name and buf:
                tests.append((name, _flush(buf)))
            name = m.group(1)
            buf = []
        elif name is not None:
            buf.append(raw)
    if name and buf:
        tests.append((name, _flush(buf)))
    return tests


def _flush(buf: list[str]) -> str:
    sql = '\n'.join(buf).strip()
    return sql.rstrip(';').strip()


def http(url: str, db: str, user: str, password: str, sql: str,
         query_id: str | None = None) -> str:
    qs = {'database': db}
    if query_id:
        qs['query_id'] = query_id
    full = f'{url}/?{urllib.parse.urlencode(qs)}'
    req = urllib.request.Request(
        full,
        data=sql.encode('utf-8'),
        method='POST',
        headers={
            'X-ClickHouse-User': user,
            'X-ClickHouse-Key': password,
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode('utf-8')


def time_query(url: str, db: str, user: str, password: str, sql: str
               ) -> tuple[str, float]:
    qid = str(uuid.uuid4())
    t0 = time.perf_counter()
    http(url, db, user, password, sql, query_id=qid)
    t1 = time.perf_counter()
    return qid, (t1 - t0) * 1000


def query_log_stats(url: str, db: str, user: str, password: str, qid: str
                    ) -> dict | None:
    http(url, db, user, password, 'SYSTEM FLUSH LOGS')
    sql = (
        'SELECT read_rows, read_bytes, memory_usage '
        'FROM system.query_log '
        f"WHERE query_id = '{qid}' AND type = 'QueryFinish' "
        'LIMIT 1 FORMAT JSONEachRow'
    )
    out = http(url, db, user, password, sql).strip()
    if not out:
        return None
    return json.loads(out.splitlines()[0])


def explain(url: str, db: str, user: str, password: str, sql: str) -> str:
    return http(
        url, db, user, password,
        f'EXPLAIN indexes = 1, projections = 1\n{sql}',
    )


def detect_projection(text: str) -> str:
    # ClickHouse 24+ EXPLAIN includes "Name: <projection_name>" inside Projections block.
    m = re.search(r'\bproj_[A-Za-z0-9_]+', text)
    return m.group(0) if m else '—'


def detect_skip_indexes(text: str) -> str:
    names = sorted(set(re.findall(r'\bidx_[A-Za-z0-9_]+', text)))
    return ', '.join(names) if names else '—'


def drop_caches(url: str, db: str, user: str, password: str) -> None:
    http(url, db, user, password, 'SYSTEM DROP MARK CACHE')
    http(url, db, user, password, 'SYSTEM DROP UNCOMPRESSED CACHE')


def run_test(url: str, db: str, user: str, password: str, name: str, sql: str
             ) -> dict:
    expl = explain(url, db, user, password, sql)
    proj = detect_projection(expl)
    skip = detect_skip_indexes(expl)

    drop_caches(url, db, user, password)
    cold = [time_query(url, db, user, password, sql)[1] for _ in range(3)]

    warm_qids: list[str] = []
    warm: list[float] = []
    for _ in range(5):
        qid, ms = time_query(url, db, user, password, sql)
        warm_qids.append(qid)
        warm.append(ms)

    stats = query_log_stats(url, db, user, password, warm_qids[-1])
    return {
        'name': name,
        'cold_ms': round(statistics.median(cold), 1),
        'warm_ms': round(statistics.median(warm), 1),
        'read_rows': int(stats['read_rows']) if stats else None,
        'read_bytes': int(stats['read_bytes']) if stats else None,
        'projection': proj,
        'indexes': skip,
    }


def fmt_row(r: dict) -> str:
    rb = f"{r['read_bytes']:,}" if r['read_bytes'] is not None else '—'
    rr = f"{r['read_rows']:,}" if r['read_rows'] is not None else '—'
    return (
        f"| {r['name']} | {r['cold_ms']} | {r['warm_ms']} | "
        f"{rr} | {rb} | {r['projection']} | {r['indexes']} |"
    )


def update_testing_md(rows: list[dict]) -> None:
    section = (
        f'{RESULTS_HEADER}\n\n'
        f'_Auto-generated by `scripts/run_genes_perf.py` '
        f"({time.strftime('%Y-%m-%d %H:%M %Z')})._\n\n"
        '| Test | Cold (ms) | Warm (ms) | Read rows | Read bytes | Projection | Skip indexes |\n'
        '|---|---|---|---|---|---|---|\n'
        + '\n'.join(fmt_row(r) for r in rows)
        + '\n'
    )
    text = RESULTS_OUT.read_text() if RESULTS_OUT.exists(
    ) else '# Endpoint testing results\n\n'
    if RESULTS_HEADER in text:
        text = re.sub(
            re.escape(RESULTS_HEADER) + r'.*?(?=\n## |\Z)',
            section.rstrip(),
            text,
            count=1,
            flags=re.DOTALL,
        )
    else:
        text = text.rstrip() + '\n\n' + section
    if not text.endswith('\n'):
        text += '\n'
    RESULTS_OUT.write_text(text)


def main() -> int:
    url, db, user, password = load_config()
    tests = parse_tests(TESTS_FILE.read_text())
    print(f'Running {len(tests)} tests against {url} (db={db})',
          file=sys.stderr)
    results: list[dict] = []
    for name, sql in tests:
        print(f'  {name} ...', end=' ', flush=True, file=sys.stderr)
        try:
            r = run_test(url, db, user, password, name, sql)
            results.append(r)
            print(
                f"cold={r['cold_ms']}ms warm={r['warm_ms']}ms "
                f"proj={r['projection']} idx={r['indexes']}",
                file=sys.stderr,
            )
        except Exception as e:
            print(f'FAILED: {e}', file=sys.stderr)
            results.append({
                'name': name, 'cold_ms': '—', 'warm_ms': '—',
                'read_rows': None, 'read_bytes': None,
                'projection': '—', 'indexes': f'ERR: {str(e)[:80]}',
            })
    update_testing_md(results)
    print(f'\nResults written to {RESULTS_OUT}', file=sys.stderr)
    print()
    print('\n'.join(fmt_row(r) for r in results))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
