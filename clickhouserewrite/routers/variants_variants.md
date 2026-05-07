# `variants_variants.ts` router

**File:** `src/routers/datatypeRouters/edges/variants_variants.ts`

**Endpoints:**
- `GET /variants/variant-ld` — `findVariantLDs` (✅ ClickHouse-ported)
- `GET /variants/variant-ld/summary` — `findVariantLDSummary` (still AQL; blocked on `variants_genes` + `variants_proteins` ports)

## Highlights

- **Largest table in the catalog** — ~12B rows after symmetrization (~6B unique LD pairs × 2 directions).
- **Symmetrized PK shape** — every LD pair stored twice at import: `(A, B, …)` and `(B, A, …)`. The table is `ORDER BY (variants_1_id, ancestry, variants_2_id)`. Every LD-partner lookup is therefore a single-column equality on the PK prefix — no OR-on-two-columns, no projections, no skip indexes needed. Rationale: [`design-decisions/09-symmetrize-edge-tables.md`](../design-decisions/09-symmetrize-edge-tables.md).
- Reuses [`parseRegion`](../../src/routers/datatypeRouters/nodes/variants.ts), [`variantIDSearch`](../../src/routers/datatypeRouters/nodes/variants.ts) and the `variants` table's primary key for the variant-detail enrichment step.

## `findVariantLDs` flow

```
Input identifiers (variant_id / spdi / hgvs / ca_id / rsid)
  └─ variantIDSearch(...)  → 1..few variants_1_id values to look up
Input region
  └─ parseRegion(...)      → { chr, start, end } pushed down as subquery
                              SELECT id FROM variants WHERE chr = ? AND pos in [start, end)
        ↓
buildLDWhere(filter, params)
  ├─ variants_1_id IN ({_v_ids:Array(String)})  // point-lookup form
  │   OR variants_1_id IN (SELECT id FROM variants WHERE chr = ? …)  // region form
  ├─ ancestry = ?         (uses PK prefix)
  ├─ r2 range filter      (parsed via parseRangeFilter, parameterized as Float32)
  └─ d_prime range filter
        ↓
Step A — page query against variants_variants (PK-clustered scan)
  SELECT chr, ancestry, d_prime, r2, label, name, source, source_url,
         variants_1_id, variants_2_id,
         variants_1_rsid AS variant_1_rsid, variants_2_rsid AS variant_2_rsid,
         variants_1_base_pair AS variant_1_base_pair, variants_2_base_pair AS variant_2_base_pair
    FROM variants_variants
   WHERE …
   ORDER BY variants_1_id, ancestry, variants_2_id
   LIMIT … OFFSET …
        ↓
Step B — variant detail enrichment (always)
  Collect distinct {variants_1_id ∪ variants_2_id} from the page (≤ 2 × limit ≤ 1000 IDs).
  Single primary-key lookup on `variants`:
    SELECT … FROM variants v WHERE v.id IN ({_var_ids:Array(String)})
  Verbose mode pulls the full variantFormat record; non-verbose pulls only pos/spdi/hgvs.
        ↓
transformLDRow(row, simpleMap, verboseMap, verbose)
  - variant_1_pos / spdi / hgvs ← simpleMap[row.variants_1_id]
  - variant_2_pos / spdi / hgvs ← simpleMap[row.variants_2_id]
  - sequence_variant:
      verbose=true  → [verboseMap[row.variants_2_id]]   // single-element array
      verbose=false → "variants/<row.variants_2_id>"    // FK string
  - All other fields renamed/passed through to the OpenAPI shape.
```

## Output mapping (every OpenAPI field)

| OpenAPI field | Source |
|---|---|
| `chr`, `ancestry`, `d_prime`, `r2`, `label`, `name`, `source`, `source_url` | direct from row |
| `variant_1_base_pair`, `variant_1_rsid`, `variant_2_base_pair`, `variant_2_rsid` | renamed from `variants_*` (singular `variant_` is the API; plural `variants_` is the column) |
| `variant_1_pos`, `variant_1_spdi`, `variant_1_hgvs` | `simpleMap[row.variants_1_id]` (variants table lookup) |
| `variant_2_pos`, `variant_2_spdi`, `variant_2_hgvs` | `simpleMap[row.variants_2_id]` |
| `sequence_variant` | FK string (non-verbose) or `[fullVariant]` array (verbose) |

## Performance

Wall times against the dev server (HTTP RTT included; server-side is sub-30ms warm):

| Query | Warm |
|---|---|
| Point lookup (variant_id) | ~100ms |
| + ancestry + r2 ≥ 0.5 | ~105ms |
| Verbose mode (full variant lookup) | ~190ms |
| Region 1kb | ~85ms warm / ~2.3s cold |
| 10kb region | within 10kb cap |

`ORDER BY (variants_1_id, ancestry, variants_2_id)` makes the LIMIT-OFFSET pagination a continued range scan — page=1, page=10, page=100 are all the same warm cost. Region cold cost is the variants-table chr/pos scan; subsequent hits cache.
