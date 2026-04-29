# Core infrastructure changes

| File | What changed |
|---|---|
| `src/database.ts` | Replaced ArangoDB driver with `@clickhouse/client`. Creates a ClickHouse client using `url`, `database`, `username`, `password` from config. Sets `request_timeout: 60_000` (60s) to handle cold-start queries on unindexed data. |
| `src/env.ts` | Updated `envSchema.database` to reflect ClickHouse connection params (`url`, `name`, `username`, `password`). Removed ArangoDB-specific fields. Production env vars renamed to `IGVF_CATALOG_CLICKHOUSE_*`. |
| `config/development.json` | Points to the ClickHouse HTTP endpoint instead of ArangoDB. |
