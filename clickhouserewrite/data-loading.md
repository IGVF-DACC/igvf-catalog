# Data loading tooling

| File | Purpose |
|---|---|
| `data/db/generate_import.py` | Python script that generates ClickHouse `INSERT INTO ... SELECT ... FROM s3(...)` YAML statements from a `.sql` schema file. Handles PK→`_key`, FK→`_from`/`_to` transforms, backtick-quoting for special column names, and uses actual SQL types for S3 schema fields. |
| `data/db/schema/clickhouse_import.yaml` | Collection of `INSERT` statements for all tables, aligned to the generated schemas. |

See [`collections.md`](collections.md) for the resulting table inventory.
