# Design decisions

Cross-cutting patterns and rationale for the ClickHouse port.

## General

1. [Parameterized queries for SQL injection prevention](01-parameterized-queries.md)
2. [Two-step enrichment instead of JOINs for verbose mode](02-two-step-enrichment.md)
3. [Three-query pagination for combined IGVF + GWAS results](03-three-query-pagination.md)
4. [`parseRangeFilter` for log10pvalue](04-range-filter-parsing.md)
5. [ID prefix preservation for API compatibility](05-id-prefix-preservation.md)
6. [Lean projections and the two-step query strategy](06-lean-projections.md)
7. [Materialized view lookup table for `rsid`](07-rsid-materialized-view.md)
8. [Region queries — pushed down as subquery for edges](08-region-queries.md)

## `genes_coding_variants` router specifics

1. [Paginate at the `hgvsp` level first (paginate-first strategy)](gcv-01-paginate-first.md)
2. [CVP two-step via `proj_by_cv_id` lean projection](gcv-02-cvp-two-step.md)
3. [`cvp.variants` eliminates the VCV lookup for variant-linked phenotypes](gcv-03-cvp-variants-fk.md)
4. [VCV direct lookup via `proj_by_cv_id` lean projection](gcv-04-vcv-projection.md)
5. [Score column safety for `all-scores`](gcv-05-score-column-safety.md)
6. [Score deduplication within a `protein_change` group](gcv-06-score-deduplication.md)
