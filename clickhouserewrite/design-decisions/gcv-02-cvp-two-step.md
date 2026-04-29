# CVP two-step via `proj_by_cv_id` lean projection

Applies to the [`genes_coding_variants` router](../routers/genes_coding_variants.md).

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
