# Three-query pagination for combined IGVF + GWAS results

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
