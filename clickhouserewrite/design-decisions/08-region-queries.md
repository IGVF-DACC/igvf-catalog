# Region queries — no additional indexing needed, pushed down as subquery for edges

Region queries filter by `chr` and `pos`. The `variants` table primary key is `id` (SPDI format, e.g. `NC_000015.10:32709532:T:A`), which starts with the chromosome reference sequence. This means the MergeTree sort order naturally clusters rows by chromosome, and ClickHouse can skip most granules using the primary key index alone.

For **edge endpoints** that accept `region` as input (e.g. `/variants/phenotypes?region=...`), the variant IDs are NOT materialized in TypeScript. Even a 1kb region can yield thousands of multi-allelic variant IDs, and serializing them via `sqlInList` blows past ClickHouse's `max_query_size` (262144 bytes default). Instead, the region is pushed down as a subquery on the variants table:

```sql
WHERE vp.variants_id IN (
  SELECT id FROM variants WHERE chr = {_vp_chr:String}
    AND pos >= {_vp_pos_start:Float64} AND pos < {_vp_pos_end:Float64}
)
```

ClickHouse evaluates the inner SELECT efficiently using primary-key granule pruning (variants is sorted by SPDI `id`, which starts with the chromosome RefSeq accession). This pattern should be reused by every edge router that accepts `region` — never round-trip a region's variant IDs through `sqlInList`.

For latency numbers, see [`testing.md`](../testing.md).
