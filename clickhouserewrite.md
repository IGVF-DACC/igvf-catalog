# ClickHouse Rewrite Progress

## Overview

This document tracks the prototype migration of the IGVF Catalog API from ArangoDB to ClickHouse. The goal is to evaluate ClickHouse as a backend for the catalog's node and edge queries, focusing on human variants data.

## Infrastructure

- **ClickHouse server**: EC2 instance at `35.85.61.200:8123` (HTTP interface)
- **Data source**: S3 bucket `s3://igvf-catalog-parsed-collections/` containing JSONL exports from ArangoDB
- **Node.js driver**: `@clickhouse/client` (added to `package.json`)
- **Schema source of truth**: `data/db/generated_schemas/*.sql` — one `CREATE TABLE` file per collection

## Files changed

### Core infrastructure

| File | What changed |
|---|---|
| `src/database.ts` | Replaced ArangoDB driver with `@clickhouse/client`. Creates a ClickHouse client using `url`, `database`, `username`, `password` from config. Sets `request_timeout: 60_000` (60s) to handle cold-start queries on unindexed data. |
| `src/env.ts` | Updated `envSchema.database` to reflect ClickHouse connection params (`url`, `name`, `username`, `password`). Removed ArangoDB-specific fields. Production env vars renamed to `IGVF_CATALOG_CLICKHOUSE_*`. |
| `config/development.json` | Points to the ClickHouse HTTP endpoint instead of ArangoDB. |

### Routers (ported)

| File | Endpoints | Status |
|---|---|---|
| `src/routers/datatypeRouters/nodes/variants.ts` | `GET /variants`, `GET /variants/summary` | Ported and tested |
| `src/routers/datatypeRouters/edges/variants_phenotypes.ts` | `GET /phenotypes/variants`, `GET /variants/phenotypes` | Ported and tested |

### Data tooling

| File | Purpose |
|---|---|
| `data/db/generate_import.py` | Python script that generates ClickHouse `INSERT INTO ... SELECT ... FROM s3(...)` YAML statements from a `.sql` schema file. Handles PK→`_key`, FK→`_from`/`_to` transforms, backtick-quoting for special column names, and uses actual SQL types for S3 schema fields. |
| `data/db/schema/clickhouse_import.yaml` | Collection of `INSERT` statements for all tables, aligned to the generated schemas. |

## Collections loaded into ClickHouse

| Table | Row count (approx) | Needed by | Notes |
|---|---|---|---|
| `variants` | ~1.2 billion | `/variants`, `/variants/phenotypes` (verbose), `/phenotypes/variants` (verbose) | Human variants only (FAVOR + IGVF). Primary key is `id` (SPDI-like identifier). Has lean projections on `spdi`, `ca_id`, `hgvs` for fast two-step lookups. |
| `rsid_to_variant` | — | `/variants?rsid=...` | Auto-updating lookup table (materialized view). Unnests `Array(String)` rsid column into `(rsid, variant_id)` pairs sorted by `rsid`. |
| `variants_phenotypes` | Loaded | `/phenotypes/variants`, `/variants/phenotypes` | Edge table linking variants to ontology terms. FK columns: `variants_id`, `ontology_terms_id`. |
| `ontology_terms` | Loaded | `/phenotypes/variants` (phenotype name resolution) | Joined to resolve phenotype names from IDs. |
| `studies` | Loaded | `/phenotypes/variants` (verbose GWAS), `/variants/phenotypes` (verbose GWAS) | GWAS study metadata, joined in verbose mode. |
| `variants_phenotypes_studies` | Loaded | `/phenotypes/variants` (GWAS path), `/variants/phenotypes` (GWAS path) | Hyperedge table connecting variant-phenotype pairs to studies. Contains GWAS statistics (`log10pvalue`, `beta`, `p_val`, etc.). |
| `motifs` | Loaded | Not yet used by ported endpoints | Loaded as part of the import tooling validation. |

## Endpoint testing results

### `GET /api/phenotypes/variants`

| Parameters | Result | Latency |
|---|---|---|
| `phenotype_id=GO_0003674&source=IGVF&limit=2` | 2 IGVF records returned | ~500ms |
| `phenotype_id=GO_0003674&source=OpenTargets&limit=2` | `[]` (no GWAS data for this phenotype) | ~600ms |
| `phenotype_id=GO_0003674&limit=2` (no source filter) | 2 records via combined pagination | ~600ms |
| `phenotype_name=molecular_function&source=IGVF&limit=2` | 2 records (name → ID lookup) | ~1.7s |
| `method=cV2F&limit=2` (no phenotype, IGVF-only) | 2 records | ~600ms |
| `phenotype_id=GO_0003674&source=IGVF&limit=1&verbose=true` | Full variant object expanded | ~600ms |
| Pagination: `page=0` vs `page=1` | Different results | ~500ms each |

### `GET /api/variants/phenotypes`

| Parameters | Result | Latency |
|---|---|---|
| `variant_id=NC_000001.11:91420:T:C&limit=3` | 3 IGVF records | ~600ms |
| `variant_id=NC_000001.11:91420:T:C&limit=1&verbose=true` | Full variant object expanded | ~3.6s |
| `rsid=rs58658771&limit=2` | 2 records (via rsid lookup table) | ~350ms |

## Design decisions

### 1. Parameterized queries for SQL injection prevention

The `variants.ts` prototype used an `esc()` helper with string interpolation to build SQL. For `variants_phenotypes.ts`, we switched to ClickHouse's native parameterized queries using the `{name:Type}` syntax with `query_params`:

```typescript
async function chQuery<T = any>(sql: string, params?: QueryParams): Promise<T[]> {
  const resultSet = await db.query({
    query: sql,
    query_params: params,
    format: 'JSONEachRow'
  })
  return await resultSet.json()
}
```

All user-supplied values (phenotype IDs, method, class, label, fileset names) go through `query_params` and are never interpolated into the SQL string. This eliminates SQL injection by design.

The one exception is the `sqlInList()` helper used for arrays of internal IDs (from `variantIDSearch()` or the VP page query). These IDs originate from our own database queries, not from user input, and are single-quote escaped as a safety measure.

### 2. Two-step enrichment instead of JOINs for verbose mode

The initial implementation joined the `variants` table directly in the query:

```sql
SELECT ... FROM variants_phenotypes vp
LEFT JOIN variants v ON v.id = vp.variants_id  -- 1.2B rows!
WHERE ...
```

This caused ClickHouse to build a hash table from the entire `variants` table (1.2B rows) in memory, resulting in a 60-second timeout. ClickHouse's hash JOIN loads the right-side table entirely into memory before evaluating the join condition.

The fix uses a two-step approach:

1. Run the base query (no variant/study JOINs) to get the page of results
2. Collect unique `variants_id` and `studies_id` values from results
3. Batch-fetch details using primary key lookups: `SELECT ... FROM variants WHERE id IN ('id1', 'id2', ...)`
4. Merge in TypeScript using `Map<string, any>`

Since the page size is at most 100 rows, the `IN` clause in step 3 contains at most 100 IDs, and the primary key lookup is fast. This brought verbose mode from 60s timeout to ~600ms for the phenotypes endpoint and ~3.6s for the variants endpoint (the extra time comes from `variantIDSearch` which must scan the variants table for the initial ID resolution).

### 3. Three-query pagination for combined IGVF + GWAS results

When no `source` filter is specified, both IGVF and GWAS records need to be returned with correct pagination. IGVF and GWAS results have different schemas (IGVF has `score`; GWAS has `log10pvalue`, `beta`, study references, etc.), making a `UNION ALL` cumbersome.

The approach:

1. **Page query**: Fetch the VP record IDs for the current page, including their `source`:
   ```sql
   SELECT vp.id, vp.source FROM variants_phenotypes vp
   WHERE ... ORDER BY vp.id LIMIT {lim} OFFSET {off}
   ```
2. **Detail queries**: Split the IDs by source and run IGVF and GWAS detail queries in parallel
3. **Merge**: Reconstruct results in the original page order using a `Map`

This gives correct global pagination across both sources — the VP table is the source of ordering, and each VP record produces either an IGVF or GWAS result.

When `source` is explicitly specified (the common case for API consumers), this simplifies to a single query.

### 4. `parseRangeFilter` for log10pvalue

The original AQL code used `getFilterStatements()` to parse range expressions. The ClickHouse version has a standalone `parseRangeFilter()` that supports `gte:5`, `lt:10`, `range:5-10`, and bare numbers. It returns a structured object used by `pvalueCondition()` to build parameterized SQL conditions:

```typescript
// Input: "gte:5" → Output: vps.log10pvalue >= {_pval:Float64} with params { _pval: 5 }
// Input: "range:5-10" → Output: vps.log10pvalue >= {_pval_lo:Float64} AND ... < {_pval_hi:Float64}
```

### 5. ID prefix preservation for API compatibility

In ArangoDB, `record._from` returns values like `variants/NC_000001.11:91420:T:C`. In ClickHouse, the FK column `variants_id` stores just `NC_000001.11:91420:T:C`. API consumers may depend on the collection prefix, so non-verbose mode prepends it:

```typescript
variant: `variants/${row.variants_id}`
study: `studies/${row.studies_id}`
```

### 6. Lean projections and the two-step query strategy

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

**Performance results (API round-trip, 1.2B rows):**

| Column | Cold cache | Warm cache |
|--------|-----------|------------|
| `spdi` | ~60ms | ~130ms |
| `ca_id` | ~60ms | ~90ms |
| `hgvs` | ~110ms | ~120ms |

### 7. Materialized view lookup table for `rsid`

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

### 8. Region queries — no additional indexing needed

Region queries filter by `chr` and `pos`. The `variants` table primary key is `id` (SPDI format, e.g. `NC_000015.10:32709532:T:A`), which starts with the chromosome reference sequence. This means the MergeTree sort order naturally clusters rows by chromosome, and ClickHouse can skip most granules using the primary key index alone.

**Performance (API round-trip, up to 10kb regions):**

| Region size | Cold cache | Warm cache |
|------------|-----------|------------|
| 100bp | ~1.7s | ~270ms |
| 1kb | ~1.9s | ~226ms |
| 5kb | ~1.8-4.1s | ~475ms |
| 10kb | ~1.6-3.5s | ~265-291ms |

## Architecture of the `variants_phenotypes.ts` router

The router is structured in layers:

```
Input parsing (extractPagination, extractVpFilter)
    ↓
Condition building (buildVpWhere + parameterized params)
    ↓
Query execution (queryIgvfRows / queryGwasRows / queryByIds)
    ↓
Enrichment (fetchVariantDetails / fetchStudyDetails — only for verbose)
    ↓
Row transformation (toIgvfResult / toGwasResult)
    ↓
Output (Zod-validated tRPC response)
```

The Zod schemas, tRPC route definitions, and `variantQueryValidation` function were kept unchanged from the ArangoDB version. The `variantIDSearch` import from `variants.ts` (already migrated) is reused as-is.

## Known limitations

1. **Large IN clauses** from `variantIDSearch()` region queries could produce thousands of IDs. Currently acceptable since regions are capped at 10kb, but a subquery or temp table approach would be more robust.
2. **Other routers still use ArangoDB types**: Files like `coding_variants_phenotypes.ts`, `diseases_genes.ts`, etc. still call `db.query(string)` with ArangoDB's `Database` type, producing TypeScript errors. These are not yet ported.
3. **No mouse variant support**: The rewrite focuses on human variants only. Mouse variant logic was removed from `variants.ts`.
4. **`ontology_terms` JOIN performance**: The `ontology_terms` table is small enough for hash JOINs, but this assumption should be validated as data grows.
5. **Cold-cache latency for region queries**: Region queries take 1.5-4s on cold cache due to reading `annotations` JSON from disk. A lean projection `ORDER BY chr, pos` could help if needed, but current performance is acceptable.

## What remains to port

All other routers in `src/routers/datatypeRouters/edges/` and `src/routers/datatypeRouters/nodes/` still use AQL. The pattern established by `variants.ts` and `variants_phenotypes.ts` can be followed for each:

1. Replace AQL with parameterized ClickHouse SQL
2. Use `chQuery()` with `query_params` for all user input
3. Use two-step enrichment for verbose mode JOINs against large tables
4. Use three-query pagination for endpoints that merge results from multiple sources
5. Use lean projections + two-step ID resolution for high-cardinality string lookups on large tables
6. Use materialized view lookup tables for array column lookups (e.g. `rsid`)
