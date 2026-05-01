# Known limitations

1. **Other routers still use ArangoDB types**: Files like `coding_variants_phenotypes.ts`, `diseases_genes.ts`, etc. still call `db.query(string)` with ArangoDB's `Database` type, producing TypeScript errors. These are not yet ported.
2. **No mouse variant support**: The rewrite focuses on human variants only. Mouse variant logic was removed from `variants.ts`. Mouse *gene* data is being loaded into the `genes` table; once present it will work through the same code path filtered by `organism`.
3. **`ontology_terms` JOIN performance**: The `ontology_terms` table is small enough for hash JOINs, but this assumption should be validated as data grows.
4. **Cold-cache latency for region queries**: Region queries take 1.5-4s on cold cache due to reading `annotations` JSON from disk. A lean projection `ORDER BY chr, pos` could help if needed, but current performance is acceptable.
5. **Coding variants with no genomic variant link**: Some `hgvsp` groups have an empty `variants[]` array. This happens when neither `cvp.variants` is populated nor a VCV entry exists for those coding variants. This is a data-coverage issue, not a query bug.
6. **`coding_variants` gene name resolution drops fuzzy matching**: The original AQL endpoint used a Levenshtein/BM25 fuzzy fallback for gene name resolution. The ClickHouse port uses exact match only (no text indexes). Unmatched gene names return `[]` instead of a fuzzy suggestion. (The standalone `/genes` endpoint *does* have fuzzy via `editDistanceUTF8`; only the `coding_variants` cross-reference path skipped it.)
