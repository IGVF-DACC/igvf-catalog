# Score deduplication within a `protein_change` group

Applies to the [`genes_coding_variants` router](../routers/genes_coding_variants.md).

Multiple coding variant IDs can share the same `hgvsp` string and map to the same genomic variant (e.g., the same nucleotide change annotated against different transcripts). When assembling the `variants[]` array, these are deduplicated by variant ID. Scores from different coding variant records for the same (variant, method, source_url) triple are deduplicated with a linear scan (bounded by methods × filesets per variant — typically ≤ 12 entries).
