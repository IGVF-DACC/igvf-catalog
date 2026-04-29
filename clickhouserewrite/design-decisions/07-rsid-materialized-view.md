# Materialized view lookup table for `rsid`

The `rsid` column is `Array(String)` — a variant can have multiple rsids, and an rsid can map to multiple variants. Projections cannot unnest arrays, so a **materialized view** provides an auto-updating lookup table:

```sql
CREATE TABLE rsid_to_variant (
    rsid String,
    variant_id String
) ENGINE = MergeTree() ORDER BY rsid;

CREATE MATERIALIZED VIEW mv_rsid_to_variant TO rsid_to_variant AS
SELECT r AS rsid, id AS variant_id
FROM variants ARRAY JOIN rsid AS r;
```

The `ARRAY JOIN` unpacks each rsid array element into a separate row. The materialized view auto-fires on every `INSERT INTO variants`, so the lookup table stays in sync without manual maintenance. Existing data is backfilled once with `INSERT INTO rsid_to_variant SELECT r, id FROM variants ARRAY JOIN rsid AS r`.

The lookup table is sorted by `rsid`, so queries are a binary search. The two-step strategy applies: `resolveViaLeanProjection()` also handles rsid by querying `rsid_to_variant` first, then fetching full variant rows by primary key.

**Performance**: rsid lookups went from 60s+ timeout to ~350-400ms cold cache, ~150ms warm cache.
