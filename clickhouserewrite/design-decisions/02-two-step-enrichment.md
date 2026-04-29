# Two-step enrichment instead of JOINs for verbose mode

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
