# Lean projections and the two-step query strategy

High-cardinality string lookups (`spdi`, `hgvs`, `ca_id`) on the 1.2 billion-row `variants` table are inherently expensive because the primary key order (`id`) does not help these filters, and the `annotations` JSON column is large (~2KB+ per row). Early approaches used bloom_filter data-skipping indexes, which reduced query times from ~55s to ~7s, and then "fat" projections (containing all columns, re-sorted by the lookup column), which achieved ~12s cold cache / ~120ms warm cache. The fat projections were slow on cold cache because each granule included the bulky `annotations` column, meaning a single lookup read ~16MB from disk.

**Lean projections** solve this by storing only the lookup column and the primary key:

```sql
ALTER TABLE variants ADD PROJECTION proj_spdi_lean (SELECT id, spdi ORDER BY spdi);
ALTER TABLE variants ADD PROJECTION proj_ca_id_lean (SELECT id, ca_id ORDER BY ca_id);
ALTER TABLE variants ADD PROJECTION proj_hgvs_lean (SELECT id, hgvs ORDER BY hgvs);
```

A lean projection granule is ~200-300KB compressed (vs ~16MB for a fat projection), making cold-cache reads near-instant (~15ms).

**Two-step query strategy** in `variants.ts`:

1. **Step 1 — Resolve IDs**: `SELECT id FROM variants WHERE spdi = {v:String}` uses the lean projection. Only reads the two-column projection data (~300KB). Returns the matching primary key(s) in ~15ms.
2. **Step 2 — Fetch full rows**: `SELECT ... FROM variants v WHERE v.id = {id:String}` uses the primary key. Reads only the specific row's data part, including annotations.

This is implemented in `resolveViaLeanProjection()` which intercepts `spdi`, `ca_id`, and `hgvs` filters before the main query, resolves them to primary key IDs, and rewrites the WHERE clause to use `v.id = ...` or `v.id IN (...)`.

For latency numbers, see [`testing.md`](../testing.md).
