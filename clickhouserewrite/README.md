# ClickHouse rewrite

This folder tracks the prototype migration of the IGVF Catalog API from ArangoDB to ClickHouse. The goal is to evaluate ClickHouse as a backend for the catalog's node and edge queries, focusing on human variants data.

## At a glance

- **ClickHouse server**: EC2 instance at `35.85.61.200:8123` (HTTP interface)
- **Data source**: S3 bucket `s3://igvf-catalog-parsed-collections/` containing JSONL exports from ArangoDB
- **Node.js driver**: `@clickhouse/client`
- **Schema source of truth**: `data/db/generated_schemas/*.sql` — one `CREATE TABLE` file per collection

For the full status of every API endpoint (port state, backing router file, OpenAPI excerpt) see [`endpoints/README.md`](endpoints/README.md). Re-run [`scripts/generate_endpoint_docs.py`](../scripts/generate_endpoint_docs.py) to refresh it after porting.

## Navigation

- [`infrastructure.md`](infrastructure.md) — `src/database.ts`, `src/env.ts`, `config/development.json`
- [`data-loading.md`](data-loading.md) — `data/db/generate_import.py` + `clickhouse_import.yaml`
- [`collections.md`](collections.md) — ClickHouse table inventory, projections, materialized views
- [`design-decisions/`](design-decisions/) — patterns and rationale (parameterized queries, two-step enrichment, lean projections, region pushdown, …)
- [`routers/`](routers/) — per-router architecture notes
- [`endpoints/`](endpoints/) — one file per OpenAPI endpoint, with status and spec excerpt
- [`testing.md`](testing.md) — endpoint test results and latency observations
- [`limitations.md`](limitations.md) — known limitations
- [`conventions.md`](conventions.md) — porting conventions for new routers

## Read this if you are…

- **…porting a new router**: read [`conventions.md`](conventions.md) and skim the relevant pages under [`design-decisions/`](design-decisions/). Cross-check the target endpoint's stub under [`endpoints/`](endpoints/).
- **…debugging a specific endpoint**: open its file under [`endpoints/`](endpoints/) — the OpenAPI excerpt and status line tell you most of what you need.
- **…doing capacity / latency work**: [`testing.md`](testing.md) and the per-design-decision latency tables.
