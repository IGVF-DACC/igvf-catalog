#!/usr/bin/env python3
"""Generate per-endpoint markdown stubs under clickhouserewrite/endpoints/.

Source of truth:
  - OpenAPI spec served by the deployed catalog API
  - Router files under src/routers/datatypeRouters/{nodes,edges}/*.ts

Output:
  - clickhouserewrite/endpoints/<slug>.md  (one per endpoint)
  - clickhouserewrite/endpoints/README.md  (index)

Re-run any time after porting more endpoints or after the OpenAPI spec changes.
The script preserves any existing "## Implementation notes" body when regenerating.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

OPENAPI_URL = 'https://catalog-api-dev.demo.igvf.org/openapi'
REPO_ROOT = Path(__file__).resolve().parent.parent
ROUTERS_DIR = REPO_ROOT / 'src' / 'routers' / 'datatypeRouters'
OUT_DIR = REPO_ROOT / 'clickhouserewrite' / 'endpoints'

# Endpoints known to error at runtime even though the code path exists.
# See clickhouserewrite/limitations.md.
BROKEN_ENDPOINTS: set[tuple[str, str]] = set()

STATUS_PORTED = '✅ ClickHouse-ported'
STATUS_AQL = '❌ AQL-only'
STATUS_MIXED = '🚧 Mixed'
STATUS_BROKEN = '⚠ Broken'
STATUS_NO_DB = 'ℹ︎ No DB call'
STATUS_UNMAPPED = '❓ Not in router files'


def fetch_openapi() -> dict:
    with urllib.request.urlopen(OPENAPI_URL, timeout=30) as r:
        return json.load(r)


def slugify(method: str, path: str) -> str:
    # /ontology-terms/{id}/children -> ontology-terms-id-children
    p = path.strip('/').replace('{', '').replace('}', '').replace('/', '-')
    return f'{method.lower()}-{p}'


def scan_routers() -> dict[tuple[str, str], dict]:
    """Map (method, path) -> {file, uses_clickhouse, uses_aql}.

    Strategy: parse each .ts file for `.meta({ openapi: { method: 'GET', path: '/foo' } })`
    and infer port style from imports / call patterns inside that file.
    """
    result: dict[tuple[str, str], dict] = {}
    meta_re = re.compile(
        r"\.meta\(\s*\{\s*openapi\s*:\s*\{[^}]*?method\s*:\s*['\"]([A-Z]+)['\"][^}]*?path\s*:\s*['\"]([^'\"]+)['\"]",
        re.DOTALL,
    )
    for ts in sorted(ROUTERS_DIR.rglob('*.ts')):
        if '__tests__' in ts.parts or ts.name.startswith('_'):
            continue
        text = ts.read_text()
        uses_clickhouse = (
            'clickhouse_helpers' in text or '@clickhouse/client' in text or 'chQuery(' in text
        )
        # Any direct call to db.query( in a router file means AQL — chQuery is the
        # ClickHouse wrapper and lives in clickhouse_helpers.ts (not scanned here).
        uses_aql = bool(
            re.search(r'\bdb\.query\(', text)
            or re.search(r'\bgetDBReturnStatements\b', text)
            or re.search(r'\bgetFilterStatements\b', text)
        )
        for m in meta_re.finditer(text):
            method = m.group(1).lower()
            path = m.group(2)
            result[(method, path)] = {
                'file': str(ts.relative_to(REPO_ROOT)),
                'uses_clickhouse': uses_clickhouse,
                'uses_aql': uses_aql,
            }
    return result


def status_for(method: str, path: str, router_info: dict | None) -> str:
    if (method, path) in BROKEN_ENDPOINTS:
        return STATUS_BROKEN
    if router_info is None:
        return STATUS_UNMAPPED
    ch = router_info['uses_clickhouse']
    aql = router_info['uses_aql']
    if ch and aql:
        return STATUS_MIXED
    if ch:
        return STATUS_PORTED
    if aql:
        return STATUS_AQL
    return STATUS_NO_DB


def render_op_excerpt(op: dict) -> str:
    return json.dumps(op, indent=2, ensure_ascii=False)


IMPL_NOTES_RE = re.compile(r'## Implementation notes\n(.*)$', re.DOTALL)


def existing_impl_notes(file: Path) -> str | None:
    if not file.exists():
        return None
    m = IMPL_NOTES_RE.search(file.read_text())
    if not m:
        return None
    body = m.group(1).strip()
    if not body or body == '(none yet)':
        return None
    return body


def render_endpoint_doc(method: str, path: str, op: dict, status: str, router_info: dict | None,
                        preserved_notes: str | None) -> str:
    summary = op.get('summary', '').strip()
    description = (op.get('description', '') or '').strip()
    router_line = (
        f"[`{router_info['file']}`](../../{router_info['file']})" if router_info else '_(not found in router files)_'
    )
    desc_block = ''
    if summary:
        desc_block += f'**Summary:** {summary}\n\n'
    if description:
        desc_block += description + '\n'
    if not desc_block:
        desc_block = '_(no description in OpenAPI spec)_\n'

    notes_body = preserved_notes if preserved_notes else '_(none yet)_'

    return f"""# `{method.upper()} {path}`

**Status:** {status}

**Router file:** {router_line}

## Description

{desc_block}
## OpenAPI excerpt

```json
{render_op_excerpt(op)}
```

## Implementation notes

{notes_body}
"""


SEGMENT_RE = re.compile(r'^/([^/]+)')


def top_segment(path: str) -> str:
    m = SEGMENT_RE.match(path)
    return m.group(1) if m else '(root)'


def render_index(rows: list[dict]) -> str:
    by_segment: dict[str, list[dict]] = {}
    for r in rows:
        by_segment.setdefault(top_segment(r['path']), []).append(r)

    out: list[str] = [
        '# Endpoints index',
        '',
        f'Auto-generated from `{OPENAPI_URL}`. Re-run `scripts/generate_endpoint_docs.py` to refresh.',
        '',
        '**Status legend:** '
        + ' · '.join([STATUS_PORTED, STATUS_MIXED, STATUS_AQL,
                     STATUS_BROKEN, STATUS_NO_DB, STATUS_UNMAPPED]),
        '',
    ]
    counts: dict[str, int] = {}
    for r in rows:
        counts[r['status']] = counts.get(r['status'], 0) + 1
    out.append('**Counts:** ' +
               ', '.join(f'{s} = {n}' for s, n in sorted(counts.items())))
    out.append('')

    for seg in sorted(by_segment.keys()):
        out.append(f'## /{seg}')
        out.append('')
        out.append('| Method | Path | Status | Router |')
        out.append('|---|---|---|---|')
        for r in sorted(by_segment[seg], key=lambda x: (x['path'], x['method'])):
            method = r['method'].upper()
            slug = r['slug']
            router = (
                f"[`{r['router_file']}`](../../{r['router_file']})" if r['router_file'] else '_—_'
            )
            out.append(
                f"| {method} | [`{r['path']}`]({slug}.md) | {r['status']} | {router} |")
        out.append('')
    return '\n'.join(out)


def main() -> int:
    print(f'Fetching {OPENAPI_URL} ...', file=sys.stderr)
    spec = fetch_openapi()
    paths = spec.get('paths', {})
    print(f'  {len(paths)} paths', file=sys.stderr)

    print('Scanning routers ...', file=sys.stderr)
    router_map = scan_routers()
    print(
        f'  {len(router_map)} (method, path) entries found in router files', file=sys.stderr)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    written = 0
    for path, ops in paths.items():
        for method, op in ops.items():
            if method.lower() not in {'get', 'post', 'put', 'delete', 'patch'}:
                continue
            method_l = method.lower()
            slug = slugify(method_l, path)
            out_file = OUT_DIR / f'{slug}.md'
            router_info = router_map.get((method_l, path))
            status = status_for(method_l, path, router_info)
            preserved = existing_impl_notes(out_file)
            doc = render_endpoint_doc(
                method_l, path, op, status, router_info, preserved)
            out_file.write_text(doc)
            written += 1
            rows.append(
                {
                    'method': method_l,
                    'path': path,
                    'slug': slug,
                    'status': status,
                    'router_file': router_info['file'] if router_info else None,
                }
            )

    (OUT_DIR / 'README.md').write_text(render_index(rows))
    print(
        f'Wrote {written} endpoint stubs and README.md to {OUT_DIR}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
