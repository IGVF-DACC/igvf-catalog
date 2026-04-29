# `genes_coding_variants.ts` router

**File:** `src/routers/datatypeRouters/edges/genes_coding_variants.ts`

**Endpoints:**
- `GET /genes/coding-variants/scores`
- `GET /genes/coding-variants/all-scores`

## End-to-end flow

The router serves both endpoints backed by four ClickHouse tables (see [collections.md](../collections.md)):

```
resolveGene(input)  →  genes table  →  { name }
        ↓
Step A: paginate hgvsp values  →  coding_variants  (or IN subquery via cvp for filtered path)
        ↓
Step B: CV metadata for page   →  coding_variants  WHERE hgvsp IN (≤25 values)
        ↓
Step C1: CVP primary keys      →  coding_variants_phenotypes  proj_by_cv_id
        |                          WHERE coding_variants_id IN (bounded list) → returns CVP ids
        ↓
Step C2: CVP full rows         →  coding_variants_phenotypes  WHERE id IN (C1 ids)
        |                          [+ optional method/fileset filter]
        ↓ (cvp.variants populated?)
        ├─ YES (SGE etc.) → variant ID extracted directly from cvp.variants
        └─ NO (MutPred2, ESM-1v) → Step D: VCV lookup  proj_by_cv_id
                                            WHERE coding_variants_id IN (bounded list)
        ↓
Step E: variant objects        →  variants  WHERE id IN (bounded list)
        ↓
Step F: assemble output in TypeScript (group by hgvsp, deduplicate by variant_id)
```

## Design decisions

1. [Paginate at the `hgvsp` level first](../design-decisions/gcv-01-paginate-first.md) — bounds all subsequent IN lists to a small number of IDs.
2. [CVP two-step via `proj_by_cv_id` lean projection](../design-decisions/gcv-02-cvp-two-step.md) — Step C, plus the two-level subquery used for filtered Step A and `findAllCodingVariantsFromGenes`.
3. [`cvp.variants` eliminates the VCV lookup for variant-linked phenotypes](../design-decisions/gcv-03-cvp-variants-fk.md) — SGE / VAMP-seq records skip Step D entirely.
4. [VCV direct lookup via `proj_by_cv_id` lean projection](../design-decisions/gcv-04-vcv-projection.md) — Step D for protein-level phenotypes (MutPred2, ESM-1v).
5. [Score column safety for `all-scores`](../design-decisions/gcv-05-score-column-safety.md) — column name comes from a static map keyed on the Zod-validated dataset enum.
6. [Score deduplication within a `protein_change` group](../design-decisions/gcv-06-score-deduplication.md) — multiple coding variants can share the same hgvsp + genomic variant.
