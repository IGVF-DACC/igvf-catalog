# `genes.ts` router

**File:** `src/routers/datatypeRouters/nodes/genes.ts`

**Endpoints:**
- `GET /genes` — `geneSearch`
- (internal) `nearestGeneSearch` — used by `/variants/summary` via `variants.ts`

## Highlights

- One ClickHouse query per identifier or name search. Replaces the AQL three-tier "exact, then text-index, then Levenshtein" flow.
- Uses materialized `name_lower` / `symbol_lower` / `synonyms_lower` columns + bloom-filter skip indexes (`idx_gene_id`, `idx_hgnc`, `idx_entrez`, `idx_name_lower`, `idx_symbol_lower`, `idx_synonyms_lower`) and a `(chr, start)` projection (`proj_by_chr_start`). DDL: [`data/db/genes_indexes.sql`](../../data/db/genes_indexes.sql).
- `parseRegion()` is reused from `variants.ts`.

## `geneSearch` flow

```
buildGenesWhere(input, params)
  ├─ organism = 'Homo sapiens' (default)
  ├─ gene_id  → (id = ? OR gene_id = ?)        // unversioned hits PK; versioned hits idx_gene_id
  ├─ hgnc_id  → hgnc = 'HGNC:…'                // prefix normalized
  ├─ entrez   → entrez = 'ENTREZ:…'            // prefix normalized
  ├─ name     → unified-search OR group:
  │             name_lower = q
  │             OR symbol_lower = q
  │             OR has(synonyms_lower, q)
  │             OR (length-prefilter AND editDistanceUTF8(name_lower, q) ≤ 2)
  │             OR (length-prefilter AND editDistanceUTF8(symbol_lower, q) ≤ 2)
  │             OR arrayExists(s -> length-prefilter AND editDistanceUTF8(s, q) ≤ 2, synonyms_lower)
  ├─ synonym  → has(synonyms_lower, lower(q))  // independent of `name`
  ├─ region   → chr = ? AND end > start AND start < end
  └─ gene_type / collection / study_set        // additional AND-filters
        ↓
SELECT GENE_SELECT [, SCORE_EXPR]
FROM genes g
WHERE …
ORDER BY [ _score, ] id
LIMIT … OFFSET …
        ↓
transformGeneRow()  // empties → null
```

### Score expression (only applied when `name` is present)

```
multiIf(
  name_lower = q, 0,                                    // exact name
  symbol_lower = q, 0,                                  // exact symbol
  has(synonyms_lower, q), 1,                            // exact synonym
  least(                                                // fuzzy: min over name, symbol, and any
    editDistanceUTF8(name_lower, q),                    //  length-prefiltered synonym; sentinel
    editDistanceUTF8(symbol_lower, q),                  //  4294967295 in arrayConcat handles
    arrayMin(arrayConcat(                               //  empty synonym arrays without falsely
      [toUInt64(4294967295)],                           //  promoting them to score 2.
      arrayMap(s -> toUInt64(editDistanceUTF8(s, q)),
        arrayFilter(s -> abs(toInt32(length(s)) - toInt32(length(q))) <= 2,
          synonyms_lower))
    ))
  ) + 2
) AS _score
```

Reachable scores: `{0, 1, 3, 4}`. Score `2` is structurally unreachable (anything with edit distance 0 would have hit one of the exact branches).

`ORDER BY _score, id` lays out: exact name/symbol first, then exact synonyms, then 1-edit fuzzy, then 2-edit fuzzy. `id` is the PK so it's a free tiebreaker for stable pagination.

## `nearestGeneSearch` flow (for `/variants/summary`)

Two-phase, both phases hit `proj_by_chr_start` and only read columns the projection covers (`GENE_SELECT_NEAREST`):

```
Phase 1: any gene whose body overlaps the input region
  SELECT … FROM genes g
   WHERE g.chr = ? AND g.end > start AND g.start < end [+ gene_type filter]
        ↓ if results, return them
Phase 2: nearest left + nearest right (parallel)
  SELECT … FROM genes g
   WHERE g.chr = ? AND g.end < start [+ gene_type] ORDER BY g.end DESC LIMIT 1
  SELECT … FROM genes g
   WHERE g.chr = ? AND g.start > end [+ gene_type] ORDER BY g.start ASC LIMIT 1
        ↓
return [left, right]
```

The wrapper `nearestGenes()` in `variants.ts` calls this twice — once unrestricted to find the nearest gene of any type, once with `gene_type=protein_coding` to find the nearest coding gene — and computes `distance` against the variant's `pos` in TypeScript.

## Output transformation

`transformGeneRow()` maps the ClickHouse row to the OpenAPI response shape. ClickHouse returns `''` for missing strings and `[]` for missing arrays (the table has no `Nullable` columns); the Zod `geneFormat` declares the optional fields as `.nullable()`, so we map `''` → `null` and `[]` → `null` for `gene_type`, `strand`, `hgnc`, `entrez`, `collections`, `study_sets`, `synonyms`. Required fields (`_id`, `chr`, `name`, `source`, `version`, `source_url`) pass through unchanged.

`gene_id` (versioned Ensembl) and `organism` are excluded from `GENE_SELECT` via `skipFields` because `geneFormat` has `additionalProperties: false`.

## Performance

See [`testing.md`](../testing.md) "Genes table indexing benchmarks". Identifier lookups read 1 granule (~60ms warm, dominated by HTTP RTT). Region/nearest-gene queries use the projection (~600KB read). The unified-search shape (T12) is the slowest at ~200ms, dominated by editDistance evaluation; the length prefilter inside the WHERE keeps the editDistance call from running on rows whose length difference already excludes them.
