# Endpoint testing results

Latency numbers are end-to-end API round-trip from a localhost client.

## `GET /api/phenotypes/variants`

| Parameters | Result | Latency |
|---|---|---|
| `phenotype_id=GO_0003674&source=IGVF&limit=2` | 2 IGVF records with all fields | ~500ms |
| `phenotype_id=GO_0003674&source=OpenTargets&limit=2` | `[]` (no GWAS data for this phenotype) | ~600ms |
| `phenotype_id=GO_0003674&limit=2` (no source filter) | 2 records via combined pagination | ~600ms |
| `phenotype_name=molecular_function&source=IGVF&limit=2` | 2 records (name → ID lookup) | ~1.7s |
| `method=cV2F&limit=2` (no phenotype, IGVF-only) | 2 records with `phenotype_id`, `files_filesets`, `biosample_term`, `biological_context` | ~600ms |
| `phenotype_id=GO_0003674&source=IGVF&limit=1&verbose=true` | Full variant object expanded | ~600ms |
| Pagination: `page=0` vs `page=1` | Different results | ~500ms each |

## `GET /api/variants/phenotypes`

| Parameters | Result | Latency |
|---|---|---|
| `variant_id=NC_000001.11:91420:T:C&limit=3` | 3 IGVF records with all fields | ~600ms |
| `variant_id=NC_000001.11:91420:T:C&limit=1&method=cV2F` | FK string for `variant` in non-verbose mode | ~600ms |
| `variant_id=NC_000001.11:91420:T:C&limit=1&verbose=true` | Full variant object expanded | ~3.6s |
| `rsid=rs58658771&limit=2` | 2 records (via rsid lookup table) | ~350ms |
| `region=chr19:44908100-44909100&limit=3` (1kb) | 3 records via region-subquery push-down | ~150ms |
| `region=chr19:44900000-44910000&limit=5` (10kb) | 5 records | ~2.4s |

## `GET /api/genes/coding-variants/scores`

| Parameters | Result | Latency |
|---|---|---|
| `gene_id=ENSG00000164308&limit=2` | ERAP2 — 2 protein_change groups with variants and scores | fast |
| `gene_id=ENSG00000139618&limit=2` | BRCA2 (large gene, 563K coding variants) — 2 records | fast |
| `gene_id=ENSG00000164308&method=MutPred2&limit=3` | Method-filtered results, only MutPred2 scores | fast |
| `gene_name=BRCA2&limit=2` | Gene name resolution path | fast |

## `GET /api/genes/coding-variants/all-scores`

| Parameters | Result | Latency |
|---|---|---|
| `gene_id=ENSG00000164308&dataset=ESM-1v&limit=5` | ERAP2 — descending ESM-1v scores | fast |
| `gene_id=ENSG00000139618&dataset=MutPred2&limit=5` | BRCA2 — descending MutPred2 scores | fast |

## Variants table — lookup performance (1.2B rows)

| Column | Cold cache | Warm cache |
|--------|-----------|------------|
| `spdi` | ~60ms | ~130ms |
| `ca_id` | ~60ms | ~90ms |
| `hgvs` | ~110ms | ~120ms |

## Region queries (up to 10kb)

| Region size | Cold cache | Warm cache |
|------------|-----------|------------|
| 100bp | ~1.7s | ~270ms |
| 1kb | ~1.9s | ~226ms |
| 5kb | ~1.8-4.1s | ~475ms |
| 10kb | ~1.6-3.5s | ~265-291ms |

## rsid lookups

Went from 60s+ timeout to ~350-400ms cold cache, ~150ms warm cache after introducing the `rsid_to_variant` materialized view.
