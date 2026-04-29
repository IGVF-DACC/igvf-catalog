# VCV direct lookup via `proj_by_cv_id` lean projection

Applies to the [`genes_coding_variants` router](../routers/genes_coding_variants.md).

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
