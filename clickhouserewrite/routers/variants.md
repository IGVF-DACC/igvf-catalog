# `variants.ts` router

**File:** `src/routers/datatypeRouters/nodes/variants.ts`

**Endpoints:**
- `GET /variants` — ✅ ported
- `GET /variants/summary` — ⚠ broken (see [limitations.md](../limitations.md#1-variantssummary-is-broken))

## Highlights

- Uses [parameterized queries](../design-decisions/01-parameterized-queries.md) end-to-end.
- High-cardinality identifier lookups (`spdi`, `hgvs`, `ca_id`) go through `resolveViaLeanProjection()` which uses [lean projections + two-step ID resolution](../design-decisions/06-lean-projections.md).
- `rsid` lookups go through `findVariantIDByRSID()` which queries the [`rsid_to_variant` materialized view](../design-decisions/07-rsid-materialized-view.md).
- Region queries rely on the `variants` table's natural [chromosome clustering via the SPDI primary key](../design-decisions/08-region-queries.md). For edge endpoints accepting `region`, the same query is pushed down as a subquery to avoid materializing thousands of IDs.
- Exports `variantIDSearch()`, `findVariantIDBySpdi()`, `findVariantIDByRSID()`, `findVariantIDByHgvs()`, `findVariantIDsByRegion()`, and `parseRegion()` for reuse by edge routers — this is the one place edge routers should resolve variant identifiers from user input.
