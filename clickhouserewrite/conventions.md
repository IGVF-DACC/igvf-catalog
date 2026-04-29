# Porting conventions

All other routers in `src/routers/datatypeRouters/edges/` and `src/routers/datatypeRouters/nodes/` still use AQL. The pattern established by `variants.ts` and `variants_phenotypes.ts` can be followed for each:

1. Replace AQL with parameterized ClickHouse SQL — see [design-decisions/01-parameterized-queries.md](design-decisions/01-parameterized-queries.md)
2. Use `chQuery()` with `query_params` for all user input
3. Use two-step enrichment for verbose mode JOINs against large tables — see [design-decisions/02-two-step-enrichment.md](design-decisions/02-two-step-enrichment.md)
4. Use three-query pagination for endpoints that merge results from multiple sources — see [design-decisions/03-three-query-pagination.md](design-decisions/03-three-query-pagination.md)
5. Use lean projections + two-step ID resolution for high-cardinality string lookups on large tables — see [design-decisions/06-lean-projections.md](design-decisions/06-lean-projections.md)
6. Use materialized view lookup tables for array column lookups (e.g. `rsid`) — see [design-decisions/07-rsid-materialized-view.md](design-decisions/07-rsid-materialized-view.md)
7. Push regions down as subqueries on the `variants` table for edge endpoints — see [design-decisions/08-region-queries.md](design-decisions/08-region-queries.md)

## Important: always use optimized variant lookups

Any endpoint that resolves variant identifiers (`spdi`, `hgvs`, `ca_id`, `rsid`) to variant IDs **must** use the optimized lookup paths — lean projections for `spdi`/`hgvs`/`ca_id` and the `rsid_to_variant` materialized view for `rsid`. Never query the `variants` table directly with `WHERE spdi = ...`, `WHERE hgvs = ...`, or `WHERE has(rsid, ...)` when selecting full rows or when used as a subquery without the lean projection.

This applies to both direct variant queries (`/variants`) and any edge endpoint that accepts variant identifiers as input (e.g. `/variants/phenotypes`, `/variants/genes`, etc.). The `variantIDSearch()` and `findVariantIDByRSID()` functions in `variants.ts` already use the optimized paths and should be reused by all edge routers that resolve variant identifiers. Bypassing these functions with direct `has(rsid, ...)` or unaliased `WHERE spdi = ...` queries against the 1.2B-row `variants` table will result in 60s+ timeouts.
