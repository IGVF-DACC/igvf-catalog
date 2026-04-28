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
| `src/routers/datatypeRouters/nodes/variants.ts` | `GET /variants`, `GET /variants/summary` | `/variants` ported and tested. `/variants/summary` currently broken — depends on `nearestGeneSearch` from the unported `genes.ts` (see limitations). |
| `src/routers/datatypeRouters/edges/variants_phenotypes.ts` | `GET /phenotypes/variants`, `GET /variants/phenotypes` | Ported and tested |
| `src/routers/datatypeRouters/edges/genes_coding_variants.ts` | `GET /genes/coding-variants/scores`, `GET /genes/coding-variants/all-scores` | Ported and tested |

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
| `coding_variants` | ~1.56B rows | `/genes/coding-variants/scores`, `/genes/coding-variants/all-scores` | Protein-level coding variant records. `id` = `{gene_name}_{transcript}_{hgvsp}_{hgvsc}` — gene name is the id prefix, enabling implicit PK clustering per gene. |
| `coding_variants_phenotypes` | ~1.1B rows | `/genes/coding-variants/scores`, `/genes/coding-variants/all-scores` | Edge table from coding variants to ontology terms (phenotypes). `id` = `{coding_variants_id}_{ontology_term}_{fileset}`. The `variants` column stores the linked genomic variant FK for assay types where the phenotype is tied to a specific nucleotide change (SGE). Has `proj_by_cv_id` lean projection `(SELECT coding_variants_id, id ORDER BY coding_variants_id)` for efficient two-step lookup by `coding_variants_id`. |
| `variants_coding_variants` | ~1.56B rows | `/genes/coding-variants/scores` | Edge table from genomic variants to coding variants. `id` = `{variants_id}_{coding_variants_id}`. Has `proj_by_cv_id` lean projection `(SELECT coding_variants_id, variants_id ORDER BY coding_variants_id)` which fully satisfies the Step D query by primary key. |

## Endpoint testing results

### `GET /api/phenotypes/variants`

| Parameters | Result | Latency |
|---|---|---|
| `phenotype_id=GO_0003674&source=IGVF&limit=2` | 2 IGVF records with all fields | ~500ms |
| `phenotype_id=GO_0003674&source=OpenTargets&limit=2` | `[]` (no GWAS data for this phenotype) | ~600ms |
| `phenotype_id=GO_0003674&limit=2` (no source filter) | 2 records via combined pagination | ~600ms |
| `phenotype_name=molecular_function&source=IGVF&limit=2` | 2 records (name → ID lookup) | ~1.7s |
| `method=cV2F&limit=2` (no phenotype, IGVF-only) | 2 records with `phenotype_id`, `files_filesets`, `biosample_term`, `biological_context` | ~600ms |
| `phenotype_id=GO_0003674&source=IGVF&limit=1&verbose=true` | Full variant object expanded | ~600ms |
| Pagination: `page=0` vs `page=1` | Different results | ~500ms each |

### `GET /api/variants/phenotypes`

| Parameters | Result | Latency |
|---|---|---|
| `variant_id=NC_000001.11:91420:T:C&limit=3` | 3 IGVF records with all fields | ~600ms |
| `variant_id=NC_000001.11:91420:T:C&limit=1&method=cV2F` | FK string for `variant` in non-verbose mode | ~600ms |
| `variant_id=NC_000001.11:91420:T:C&limit=1&verbose=true` | Full variant object expanded | ~3.6s |
| `rsid=rs58658771&limit=2` | 2 records (via rsid lookup table) | ~350ms |
| `region=chr19:44908100-44909100&limit=3` (1kb) | 3 records via region-subquery push-down | ~150ms |
| `region=chr19:44900000-44910000&limit=5` (10kb) | 5 records | ~2.4s |

### `GET /api/genes/coding-variants/scores`

| Parameters | Result | Latency |
|---|---|---|
| `gene_id=ENSG00000164308&limit=2` | ERAP2 — 2 protein_change groups with variants and scores | fast |
| `gene_id=ENSG00000139618&limit=2` | BRCA2 (large gene, 563K coding variants) — 2 records | fast |
| `gene_id=ENSG00000164308&method=MutPred2&limit=3` | Method-filtered results, only MutPred2 scores | fast |
| `gene_name=BRCA2&limit=2` | Gene name resolution path | fast |

### `GET /api/genes/coding-variants/all-scores`

| Parameters | Result | Latency |
|---|---|---|
| `gene_id=ENSG00000164308&dataset=ESM-1v&limit=5` | ERAP2 — descending ESM-1v scores | fast |
| `gene_id=ENSG00000139618&dataset=MutPred2&limit=5` | BRCA2 — descending MutPred2 scores | fast |

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

### 8. Region queries — no additional indexing needed, pushed down as subquery for edges

Region queries filter by `chr` and `pos`. The `variants` table primary key is `id` (SPDI format, e.g. `NC_000015.10:32709532:T:A`), which starts with the chromosome reference sequence. This means the MergeTree sort order naturally clusters rows by chromosome, and ClickHouse can skip most granules using the primary key index alone.

For **edge endpoints** that accept `region` as input (e.g. `/variants/phenotypes?region=...`), the variant IDs are NOT materialized in TypeScript. Even a 1kb region can yield thousands of multi-allelic variant IDs, and serializing them via `sqlInList` blows past ClickHouse's `max_query_size` (262144 bytes default). Instead, the region is pushed down as a subquery on the variants table:

```sql
WHERE vp.variants_id IN (
  SELECT id FROM variants WHERE chr = {_vp_chr:String}
    AND pos >= {_vp_pos_start:Float64} AND pos < {_vp_pos_end:Float64}
)
```

ClickHouse evaluates the inner SELECT efficiently using primary-key granule pruning (variants is sorted by SPDI `id`, which starts with the chromosome RefSeq accession). This pattern should be reused by every edge router that accepts `region` — never round-trip a region's variant IDs through `sqlInList`.

**Performance (API round-trip, up to 10kb regions):**

| Region size | Cold cache | Warm cache |
|------------|-----------|------------|
| 100bp | ~1.7s | ~270ms |
| 1kb | ~1.9s | ~226ms |
| 5kb | ~1.8-4.1s | ~475ms |
| 10kb | ~1.6-3.5s | ~265-291ms |

## Architecture of the `genes_coding_variants.ts` router

The router serves two endpoints backed by four ClickHouse tables:

```
resolveGene(input)  →  genes table  →  { name }
        ↓
Step A: paginate hgvsp values  →  coding_variants  (or IN subquery via cvp for filtered path)
        ↓
Step B: CV metadata for page   →  coding_variants  WHERE hgvsp IN (≤25 values)
        ↓
Step C1: CVP primary keys      →  coding_variants_phenotypes  proj_by_cv_id
        |                          WHERE coding_variants_id IN (bounded list) → returns CVP ids
        ↓
Step C2: CVP full rows         →  coding_variants_phenotypes  WHERE id IN (C1 ids)
        |                          [+ optional method/fileset filter]
        ↓ (cvp.variants populated?)
        ├─ YES (SGE etc.) → variant ID extracted directly from cvp.variants
        └─ NO (MutPred2, ESM-1v) → Step D: VCV lookup  proj_by_cv_id
                                            WHERE coding_variants_id IN (bounded list)
        ↓
Step E: variant objects        →  variants  WHERE id IN (bounded list)
        ↓
Step F: assemble output in TypeScript (group by hgvsp, deduplicate by variant_id)
```

### Key design decisions

#### 1. Paginate at the `hgvsp` level first (paginate-first strategy)

The naive approach — fetch all coding variant IDs for the gene, then use them in an `IN` clause on `coding_variants_phenotypes` — fails for large genes. BRCA2 has 563K coding variants. `sqlInList(563K IDs)` produces a ~250KB SQL string that exceeds ClickHouse's `max_query_size` limit.

The fix: paginate at the `hgvsp` (amino acid change) level before touching any large table. `coding_variants` has the same 1.56B rows as `variants_coding_variants`, but since its `id` starts with the gene name, ClickHouse's MergeTree sort order clusters all rows for a gene together. A `GROUP BY hgvsp ORDER BY min(protein_id), min(aapos) LIMIT 25` on `coding_variants WHERE gene_name = ?` processes only that gene's rows and returns 25 hgvsp strings in ~50ms.

All subsequent `sqlInList` calls are now bounded:
- hgvsp strings in step B: ≤ 25
- `coding_variants_id` values in steps C and D: ≤ 25 hgvsps × ~10 CVs/hgvsp = ~250 IDs (~12KB)
- `variants_id` values in step E: similarly bounded (~250 SHA-256 hashes ~16KB)

#### 2. CVP two-step via `proj_by_cv_id` lean projection

`coding_variants_phenotypes` (1.1B rows) has a lean projection:

```sql
ALTER TABLE coding_variants_phenotypes
  ADD PROJECTION proj_by_cv_id (SELECT coding_variants_id, id ORDER BY coding_variants_id);
```

The projection stores only `(coding_variants_id, id)` sorted by `coding_variants_id`, so queries that SELECT only those two columns and filter by `coding_variants_id` are fully answered from the projection without touching the main table.

Step C uses a two-step strategy exploiting this:

**C1** — resolve CVP primary keys via projection (activeCvIds ≤ ~250):
```sql
SELECT id FROM coding_variants_phenotypes
WHERE coding_variants_id IN ('cv_id1', 'cv_id2', ...)
```
This is fully satisfiable from the projection. ClickHouse binary-searches the sorted `coding_variants_id` order and returns all matching `id` values.

**C2** — fetch full rows by primary key, apply method/fileset filters:
```sql
SELECT coding_variants_id, method, source_url, variants, CASE ... END AS score_value
FROM coding_variants_phenotypes cvp
WHERE cvp.id IN ('cvp_id1', 'cvp_id2', ...) [AND method = ...] [AND files_filesets = ...]
```
Uses the main table's primary key (`id`). Since the `id` list is bounded (~250 CVs × ~5 phenotypes each), this is fast.

For the **filtered Step A path** (when method or fileset is specified), a two-level nested subquery is required. A single `WHERE coding_variants_id IN (subquery) AND method = ?` cannot use the lean projection because `method` is not stored in it, causing a full 1.1B row scan. The correct structure separates the two concerns:

```sql
SELECT cv.hgvsp FROM coding_variants cv
WHERE cv.gene_name = {_gname:String}
  AND cv.id IN (
    -- Outer: primary key lookup; ClickHouse min/max-prunes to the gene's
    -- contiguous ID block before applying the method/fileset filter.
    SELECT DISTINCT coding_variants_id FROM coding_variants_phenotypes
    WHERE id IN (
      -- Inner: fully answered from projection (SELECT id, WHERE coding_variants_id IN).
      SELECT id FROM coding_variants_phenotypes
      WHERE coding_variants_id IN (
        SELECT id FROM coding_variants WHERE gene_name = {_gname:String}
      )
    )
    AND method = {_method:String}   -- applied after primary key narrows the scan
  )
GROUP BY cv.hgvsp ORDER BY ... LIMIT ...
```

The innermost subquery is fully satisfied by the lean projection (both `id` and `coding_variants_id` are stored there). This returns all CVP primary keys for the gene. The middle query then uses those as a primary key filter on the main table; since all a gene's CVP rows share the same ID prefix, ClickHouse's min/max pruning restricts the scan to only that gene's contiguous granule range before applying the method filter.

For **`findAllCodingVariantsFromGenes`**, the same two-level pattern scopes the score query to the gene:

```sql
SELECT cvp.${scoreCol} AS score_value FROM coding_variants_phenotypes cvp
WHERE cvp.id IN (
  SELECT id FROM coding_variants_phenotypes
  WHERE coding_variants_id IN (
    SELECT id FROM coding_variants WHERE gene_name = {_gname:String}
  )
)
AND cvp.method = {_method:String}
ORDER BY cvp.${scoreCol} DESC LIMIT ...
```

#### 3. `cvp.variants` eliminates the VCV lookup for variant-linked phenotypes

`coding_variants_phenotypes` has a `variants` column that stores the linked genomic variant FK (`variants/NC_000013.11:...`) for assay types where the phenotype is tied to a specific nucleotide change (SGE, VAMP-seq). Extracting the variant ID directly from this column eliminates a separate `variants_coding_variants` lookup for those records, avoiding the need to touch the 1.56B-row VCV table at all for SGE data.

For protein-level phenotypes (MutPred2, ESM-1v), `cvp.variants` is empty. These still require a VCV lookup.

#### 4. VCV direct lookup via `proj_by_cv_id` lean projection

`variants_coding_variants` (1.56B rows) has a lean projection:

```sql
ALTER TABLE variants_coding_variants
  ADD PROJECTION proj_by_cv_id (SELECT coding_variants_id, variants_id ORDER BY coding_variants_id);
```

The projection stores `(coding_variants_id, variants_id)` sorted by `coding_variants_id`. Both the SELECT columns (`variants_id`, `coding_variants_id`) and the WHERE column (`coding_variants_id`) are in the projection, so Step D is fully answered from it:

```sql
SELECT vcv.variants_id, vcv.coding_variants_id
FROM variants_coding_variants vcv
WHERE vcv.coding_variants_id IN ('cv_id1', 'cv_id2', ...)
LIMIT 1 BY vcv.coding_variants_id
```

This replaces the earlier `startsWith(vcv.id, chrPrefix)` approach, which required knowing the gene's chromosome and maintaining a static `CHR_TO_REFSEQ_PREFIX` map, and silently skipped the VCV lookup for genes on unplaced contigs. The projection-based approach works for all genes unconditionally.

#### 5. Score column safety for `all-scores`

`coding_variants_phenotypes` uses different column names for different scoring methods (`score`, `esm_1v_score`, `pathogenicity_score`), and all are non-nullable `Float64`. The column name is selected from a static `DATASET_SCORE_COL` map keyed on the Zod-validated `dataset` enum value — it is never interpolated from raw user input.

#### 6. Score deduplication within a `protein_change` group

Multiple coding variant IDs can share the same `hgvsp` string and map to the same genomic variant (e.g., the same nucleotide change annotated against different transcripts). When assembling the `variants[]` array, these are deduplicated by variant ID. Scores from different coding variant records for the same (variant, method, source_url) triple are deduplicated with a linear scan (bounded by methods × filesets per variant — typically ≤ 12 entries).

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

### Fields returned by IGVF (cV2F) records

The `IGVF_SELECT` constant is built by `getChSelectStatements` from the cV2F JSON schema's `accessible_via.return` list, which includes:

- `name`, `source`, `source_url`, `score`, `method`, `class`, `label` — core edge fields
- `files_filesets` — FK to the files/filesets collection (stored as `files_filesets/{IGVFFI...}`)
- `biosample_term` — ontology term FK for the biosample (stored as `ontology_terms/{...}`)
- `biological_context` — human-readable context string (e.g. `"heart"`, `"HepG2"`)

In addition, two fields are added via `extraSelect`:
- `phenotype_id` — from `vp.ontology_terms_id`, the ontology term ID of the linked phenotype
- `phenotype_term` — from `ot.name` via a JOIN on `ontology_terms`

Non-verbose mode returns `variant` as an FK string (`variants/{id}`). Verbose mode fetches the full variant object via a batch primary key lookup.

### Comparison with ArangoDB PROD

| Field | LOCAL (ClickHouse) | PROD (ArangoDB) | Match? |
|---|---|---|---|
| `name`, `source`, `source_url`, `score`, `method`, `class` | ✓ | ✓ | ✓ |
| `phenotype_term` | ✓ | ✓ | ✓ |
| `phenotype_id` | ✓ (added) | ✓ | ✓ |
| `files_filesets` | ✓ (added) | ✓ | ✓ |
| `biosample_term` | ✓ (added) | ✓ | ✓ |
| `biological_context` | ✓ (added) | ✓ | ✓ |
| `variant` (non-verbose) | FK string | FK string | ✓ |
| `variant` (verbose) | expanded object | expanded object | ✓ |

## Known limitations

1. **`/variants/summary` is broken**: The endpoint funnels every response through `nearestGenes()` in `variants.ts`, which calls `nearestGeneSearch` from the still-AQL `genes.ts`. That code does `await db.query(stringQuery)` against the ClickHouse client (which expects an object) using an AQL query body. The client throws `Cannot read properties of undefined (reading 'trim')` because it tries to read `params.query.trim()` on the string argument. Fix requires porting `nearestGeneSearch` (or inlining the gene-nearest logic in `variants.ts` against the already-loaded `genes` table). Affects all input forms (`variant_id`, `rsid`, `spdi`, `region`).
2. **Other routers still use ArangoDB types**: Files like `coding_variants_phenotypes.ts`, `diseases_genes.ts`, etc. still call `db.query(string)` with ArangoDB's `Database` type, producing TypeScript errors. These are not yet ported.
3. **No mouse variant support**: The rewrite focuses on human variants only. Mouse variant logic was removed from `variants.ts`.
4. **`ontology_terms` JOIN performance**: The `ontology_terms` table is small enough for hash JOINs, but this assumption should be validated as data grows.
5. **Cold-cache latency for region queries**: Region queries take 1.5-4s on cold cache due to reading `annotations` JSON from disk. A lean projection `ORDER BY chr, pos` could help if needed, but current performance is acceptable.
6. **Coding variants with no genomic variant link**: Some `hgvsp` groups have an empty `variants[]` array. This happens when neither `cvp.variants` is populated nor a VCV entry exists for those coding variants. This is a data-coverage issue, not a query bug.
7. **`coding_variants` gene name resolution drops fuzzy matching**: The original AQL endpoint used a Levenshtein/BM25 fuzzy fallback for gene name resolution. The ClickHouse port uses exact match only (no text indexes). Unmatched gene names return `[]` instead of a fuzzy suggestion.

## What remains to port

All other routers in `src/routers/datatypeRouters/edges/` and `src/routers/datatypeRouters/nodes/` still use AQL. The pattern established by `variants.ts` and `variants_phenotypes.ts` can be followed for each:

1. Replace AQL with parameterized ClickHouse SQL
2. Use `chQuery()` with `query_params` for all user input
3. Use two-step enrichment for verbose mode JOINs against large tables
4. Use three-query pagination for endpoints that merge results from multiple sources
5. Use lean projections + two-step ID resolution for high-cardinality string lookups on large tables
6. Use materialized view lookup tables for array column lookups (e.g. `rsid`)

### Important: always use optimized variant lookups

Any endpoint that resolves variant identifiers (`spdi`, `hgvs`, `ca_id`, `rsid`) to variant IDs **must** use the optimized lookup paths — lean projections for `spdi`/`hgvs`/`ca_id` and the `rsid_to_variant` materialized view for `rsid`. Never query the `variants` table directly with `WHERE spdi = ...`, `WHERE hgvs = ...`, or `WHERE has(rsid, ...)` when selecting full rows or when used as a subquery without the lean projection.

This applies to both direct variant queries (`/variants`) and any edge endpoint that accepts variant identifiers as input (e.g. `/variants/phenotypes`, `/variants/genes`, etc.). The `variantIDSearch()` and `findVariantIDByRSID()` functions in `variants.ts` already use the optimized paths and should be reused by all edge routers that resolve variant identifiers. Bypassing these functions with direct `has(rsid, ...)` or unaliased `WHERE spdi = ...` queries against the 1.2B-row `variants` table will result in 60s+ timeouts.
