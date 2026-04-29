# Score column safety for `all-scores`

Applies to the [`genes_coding_variants` router](../routers/genes_coding_variants.md).

`coding_variants_phenotypes` uses different column names for different scoring methods (`score`, `esm_1v_score`, `pathogenicity_score`), and all are non-nullable `Float64`. The column name is selected from a static `DATASET_SCORE_COL` map keyed on the Zod-validated `dataset` enum value — it is never interpolated from raw user input.
