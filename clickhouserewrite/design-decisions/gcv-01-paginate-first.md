# Paginate at the `hgvsp` level first (paginate-first strategy)

Applies to the [`genes_coding_variants` router](../routers/genes_coding_variants.md).

The naive approach — fetch all coding variant IDs for the gene, then use them in an `IN` clause on `coding_variants_phenotypes` — fails for large genes. BRCA2 has 563K coding variants. `sqlInList(563K IDs)` produces a ~250KB SQL string that exceeds ClickHouse's `max_query_size` limit.

The fix: paginate at the `hgvsp` (amino acid change) level before touching any large table. `coding_variants` has the same 1.56B rows as `variants_coding_variants`, but since its `id` starts with the gene name, ClickHouse's MergeTree sort order clusters all rows for a gene together. A `GROUP BY hgvsp ORDER BY min(protein_id), min(aapos) LIMIT 25` on `coding_variants WHERE gene_name = ?` processes only that gene's rows and returns 25 hgvsp strings in ~50ms.

All subsequent `sqlInList` calls are now bounded:
- hgvsp strings in step B: ≤ 25
- `coding_variants_id` values in steps C and D: ≤ 25 hgvsps × ~10 CVs/hgvsp = ~250 IDs (~12KB)
- `variants_id` values in step E: similarly bounded (~250 SHA-256 hashes ~16KB)
