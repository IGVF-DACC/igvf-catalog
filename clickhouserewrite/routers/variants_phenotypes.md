# `variants_phenotypes.ts` router

**File:** `src/routers/datatypeRouters/edges/variants_phenotypes.ts`

**Endpoints:**
- `GET /phenotypes/variants`
- `GET /variants/phenotypes`

## Layered structure

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

The Zod schemas, tRPC route definitions, and `variantQueryValidation` function were kept unchanged from the ArangoDB version. The `variantIDSearch` import from `variants.ts` is reused for non-region variant identifiers.

## Key design choices

- **Verbose mode** uses [two-step enrichment](../design-decisions/02-two-step-enrichment.md) instead of JOINs, since hash-joining the 1.2B-row `variants` table times out at 60s.
- **Combined IGVF + GWAS pagination** (when no `source` filter) uses [three-query pagination](../design-decisions/03-three-query-pagination.md): one VP page query establishes ordering, then IGVF and GWAS detail queries run in parallel.
- **`log10pvalue` range filter** is parsed by [`parseRangeFilter`](../design-decisions/04-range-filter-parsing.md) into a structured object and rendered as parameterized SQL.
- **Region inputs** are pushed down as a subquery on `variants` rather than materialized into an IN list — see [region pushdown](../design-decisions/08-region-queries.md). Without this, a 1kb region's thousands of multi-allelic IDs blow past `max_query_size`.
- **FK strings**: non-verbose mode prepends collection prefixes for [API compatibility](../design-decisions/05-id-prefix-preservation.md): `variants/{id}`, `studies/{id}`.

## IGVF (cV2F) record fields

The `IGVF_SELECT` constant is built by `getChSelectStatements` from the cV2F JSON schema's `accessible_via.return` list:

- `name`, `source`, `source_url`, `score`, `method`, `class`, `label` — core edge fields
- `files_filesets` — FK to the files/filesets collection (stored as `files_filesets/{IGVFFI...}`)
- `biosample_term` — ontology term FK for the biosample (stored as `ontology_terms/{...}`)
- `biological_context` — human-readable context string (e.g. `"heart"`, `"HepG2"`)

In addition, two fields are added via `extraSelect`:
- `phenotype_id` — from `vp.ontology_terms_id`, the ontology term ID of the linked phenotype
- `phenotype_term` — from `ot.name` via a JOIN on `ontology_terms`

Non-verbose mode returns `variant` as an FK string (`variants/{id}`). Verbose mode fetches the full variant object via a batch primary key lookup.

## Comparison with ArangoDB PROD

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
