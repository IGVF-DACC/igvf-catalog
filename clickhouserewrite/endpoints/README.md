# Endpoints index

Auto-generated from `https://catalog-api-dev.demo.igvf.org/openapi`. Re-run `scripts/generate_endpoint_docs.py` to refresh.

**Status legend:** ✅ ClickHouse-ported · 🚧 Mixed · ❌ AQL-only · ⚠ Broken · ℹ︎ No DB call · ❓ Not in router files

**Counts:** ℹ︎ No DB call = 2, ✅ ClickHouse-ported = 9, ❌ AQL-only = 58, ❓ Not in router files = 1, 🚧 Mixed = 11

## /autocomplete

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/autocomplete`](get-autocomplete.md) | ❌ AQL-only | [`src/routers/datatypeRouters/autocomplete.ts`](../../src/routers/datatypeRouters/autocomplete.ts) |

## /biosamples

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/biosamples/genomic-elements`](get-biosamples-genomic-elements.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/genomic_elements_biosamples.ts`](../../src/routers/datatypeRouters/edges/genomic_elements_biosamples.ts) |
| GET | [`/biosamples/variants`](get-biosamples-variants.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/variants_biosamples.ts`](../../src/routers/datatypeRouters/edges/variants_biosamples.ts) |

## /coding-variants

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/coding-variants`](get-coding-variants.md) | ❌ AQL-only | [`src/routers/datatypeRouters/nodes/coding_variants.ts`](../../src/routers/datatypeRouters/nodes/coding_variants.ts) |
| GET | [`/coding-variants/phenotypes`](get-coding-variants-phenotypes.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/coding_variants_phenotypes.ts`](../../src/routers/datatypeRouters/edges/coding_variants_phenotypes.ts) |
| GET | [`/coding-variants/phenotypes-count`](get-coding-variants-phenotypes-count.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/coding_variants_phenotypes.ts`](../../src/routers/datatypeRouters/edges/coding_variants_phenotypes.ts) |
| GET | [`/coding-variants/phenotypes/score-summary`](get-coding-variants-phenotypes-score-summary.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/coding_variants_phenotypes.ts`](../../src/routers/datatypeRouters/edges/coding_variants_phenotypes.ts) |
| GET | [`/coding-variants/variants`](get-coding-variants-variants.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/variants_coding_variants.ts`](../../src/routers/datatypeRouters/edges/variants_coding_variants.ts) |

## /complexes

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/complexes`](get-complexes.md) | ❌ AQL-only | [`src/routers/datatypeRouters/nodes/complexes.ts`](../../src/routers/datatypeRouters/nodes/complexes.ts) |
| GET | [`/complexes/proteins`](get-complexes-proteins.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/complexes_proteins.ts`](../../src/routers/datatypeRouters/edges/complexes_proteins.ts) |

## /diseases

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/diseases/genes`](get-diseases-genes.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/diseases_genes.ts`](../../src/routers/datatypeRouters/edges/diseases_genes.ts) |
| GET | [`/diseases/variants`](get-diseases-variants.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/variants_diseases.ts`](../../src/routers/datatypeRouters/edges/variants_diseases.ts) |

## /drugs

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/drugs`](get-drugs.md) | ❌ AQL-only | [`src/routers/datatypeRouters/nodes/drugs.ts`](../../src/routers/datatypeRouters/nodes/drugs.ts) |
| GET | [`/drugs/variants`](get-drugs-variants.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/variants_drugs.ts`](../../src/routers/datatypeRouters/edges/variants_drugs.ts) |

## /enhancer-gene-predictions

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/enhancer-gene-predictions`](get-enhancer-gene-predictions.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/enhancer_genes.ts`](../../src/routers/datatypeRouters/edges/enhancer_genes.ts) |

## /files-filesets

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/files-filesets`](get-files-filesets.md) | ❌ AQL-only | [`src/routers/datatypeRouters/nodes/files_filesets.ts`](../../src/routers/datatypeRouters/nodes/files_filesets.ts) |

## /gene-products

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/gene-products/go-terms`](get-gene-products-go-terms.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/go_terms_annotations.ts`](../../src/routers/datatypeRouters/edges/go_terms_annotations.ts) |

## /genes

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/genes`](get-genes.md) | ✅ ClickHouse-ported | [`src/routers/datatypeRouters/nodes/genes.ts`](../../src/routers/datatypeRouters/nodes/genes.ts) |
| GET | [`/genes/coding-variants/all-scores`](get-genes-coding-variants-all-scores.md) | ✅ ClickHouse-ported | [`src/routers/datatypeRouters/edges/genes_coding_variants.ts`](../../src/routers/datatypeRouters/edges/genes_coding_variants.ts) |
| GET | [`/genes/coding-variants/scores`](get-genes-coding-variants-scores.md) | ✅ ClickHouse-ported | [`src/routers/datatypeRouters/edges/genes_coding_variants.ts`](../../src/routers/datatypeRouters/edges/genes_coding_variants.ts) |
| GET | [`/genes/diseases`](get-genes-diseases.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/diseases_genes.ts`](../../src/routers/datatypeRouters/edges/diseases_genes.ts) |
| GET | [`/genes/genes`](get-genes-genes.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/genes_genes.ts`](../../src/routers/datatypeRouters/edges/genes_genes.ts) |
| GET | [`/genes/genomic-elements`](get-genes-genomic-elements.md) | 🚧 Mixed | [`src/routers/datatypeRouters/edges/genomic_elements_genes.ts`](../../src/routers/datatypeRouters/edges/genomic_elements_genes.ts) |
| GET | [`/genes/pathways`](get-genes-pathways.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/genes_pathways.ts`](../../src/routers/datatypeRouters/edges/genes_pathways.ts) |
| GET | [`/genes/proteins`](get-genes-proteins.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/genes_transcripts.ts`](../../src/routers/datatypeRouters/edges/genes_transcripts.ts) |
| GET | [`/genes/transcripts`](get-genes-transcripts.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/genes_transcripts.ts`](../../src/routers/datatypeRouters/edges/genes_transcripts.ts) |
| GET | [`/genes/variants`](get-genes-variants.md) | 🚧 Mixed | [`src/routers/datatypeRouters/edges/variants_genes.ts`](../../src/routers/datatypeRouters/edges/variants_genes.ts) |

## /genes-proteins

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/genes-proteins/genes-proteins`](get-genes-proteins-genes-proteins.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/genes_proteins_variants.ts`](../../src/routers/datatypeRouters/edges/genes_proteins_variants.ts) |
| GET | [`/genes-proteins/variants`](get-genes-proteins-variants.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/genes_proteins_variants.ts`](../../src/routers/datatypeRouters/edges/genes_proteins_variants.ts) |

## /genes-structure

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/genes-structure`](get-genes-structure.md) | ❌ AQL-only | [`src/routers/datatypeRouters/nodes/genes_structure.ts`](../../src/routers/datatypeRouters/nodes/genes_structure.ts) |

## /genomic-elements

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/genomic-elements`](get-genomic-elements.md) | ❌ AQL-only | [`src/routers/datatypeRouters/nodes/genomic_elements.ts`](../../src/routers/datatypeRouters/nodes/genomic_elements.ts) |
| GET | [`/genomic-elements/biosamples`](get-genomic-elements-biosamples.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/genomic_elements_biosamples.ts`](../../src/routers/datatypeRouters/edges/genomic_elements_biosamples.ts) |
| GET | [`/genomic-elements/genes`](get-genomic-elements-genes.md) | 🚧 Mixed | [`src/routers/datatypeRouters/edges/genomic_elements_genes.ts`](../../src/routers/datatypeRouters/edges/genomic_elements_genes.ts) |
| GET | [`/genomic-elements/variants`](get-genomic-elements-variants.md) | 🚧 Mixed | [`src/routers/datatypeRouters/edges/variants_genomic_elements.ts`](../../src/routers/datatypeRouters/edges/variants_genomic_elements.ts) |

## /go-terms

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/go-terms/gene-products`](get-go-terms-gene-products.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/go_terms_annotations.ts`](../../src/routers/datatypeRouters/edges/go_terms_annotations.ts) |

## /health

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/health`](get-health.md) | ℹ︎ No DB call | [`src/routers/datatypeRouters/nodes/health.ts`](../../src/routers/datatypeRouters/nodes/health.ts) |

## /llm-query

| Method | Path | Status | Router |
|---|---|---|---|
| POST | [`/llm-query`](post-llm-query.md) | ℹ︎ No DB call | [`src/routers/datatypeRouters/nodes/llm_query.ts`](../../src/routers/datatypeRouters/nodes/llm_query.ts) |

## /motifs

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/motifs`](get-motifs.md) | ❌ AQL-only | [`src/routers/datatypeRouters/nodes/motifs.ts`](../../src/routers/datatypeRouters/nodes/motifs.ts) |
| GET | [`/motifs/proteins`](get-motifs-proteins.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/motifs_proteins.ts`](../../src/routers/datatypeRouters/edges/motifs_proteins.ts) |

## /ontology-terms

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/ontology-terms`](get-ontology-terms.md) | ❌ AQL-only | [`src/routers/datatypeRouters/nodes/ontologies.ts`](../../src/routers/datatypeRouters/nodes/ontologies.ts) |
| GET | [`/ontology-terms/{ontology_term_id_start}/transitive-closure/{ontology_term_id_end}`](get-ontology-terms-ontology_term_id_start-transitive-closure-ontology_term_id_end.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/ontology_terms_ontology_terms.ts`](../../src/routers/datatypeRouters/edges/ontology_terms_ontology_terms.ts) |
| GET | [`/ontology-terms/{ontology_term_id}/children`](get-ontology-terms-ontology_term_id-children.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/ontology_terms_ontology_terms.ts`](../../src/routers/datatypeRouters/edges/ontology_terms_ontology_terms.ts) |
| GET | [`/ontology-terms/{ontology_term_id}/parents`](get-ontology-terms-ontology_term_id-parents.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/ontology_terms_ontology_terms.ts`](../../src/routers/datatypeRouters/edges/ontology_terms_ontology_terms.ts) |

## /pathways

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/pathways`](get-pathways.md) | ❌ AQL-only | [`src/routers/datatypeRouters/nodes/pathways.ts`](../../src/routers/datatypeRouters/nodes/pathways.ts) |
| GET | [`/pathways/genes`](get-pathways-genes.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/genes_pathways.ts`](../../src/routers/datatypeRouters/edges/genes_pathways.ts) |
| GET | [`/pathways/pathways`](get-pathways-pathways.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/pathways_pathways.ts`](../../src/routers/datatypeRouters/edges/pathways_pathways.ts) |

## /phenotypes

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/phenotypes/coding-variants`](get-phenotypes-coding-variants.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/coding_variants_phenotypes.ts`](../../src/routers/datatypeRouters/edges/coding_variants_phenotypes.ts) |
| GET | [`/phenotypes/variants`](get-phenotypes-variants.md) | ✅ ClickHouse-ported | [`src/routers/datatypeRouters/edges/variants_phenotypes.ts`](../../src/routers/datatypeRouters/edges/variants_phenotypes.ts) |

## /proteins

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/proteins`](get-proteins.md) | ❌ AQL-only | [`src/routers/datatypeRouters/nodes/proteins.ts`](../../src/routers/datatypeRouters/nodes/proteins.ts) |
| GET | [`/proteins/complexes`](get-proteins-complexes.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/complexes_proteins.ts`](../../src/routers/datatypeRouters/edges/complexes_proteins.ts) |
| GET | [`/proteins/genes`](get-proteins-genes.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/genes_transcripts.ts`](../../src/routers/datatypeRouters/edges/genes_transcripts.ts) |
| GET | [`/proteins/motifs`](get-proteins-motifs.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/motifs_proteins.ts`](../../src/routers/datatypeRouters/edges/motifs_proteins.ts) |
| GET | [`/proteins/proteins`](get-proteins-proteins.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/proteins_proteins.ts`](../../src/routers/datatypeRouters/edges/proteins_proteins.ts) |
| GET | [`/proteins/transcripts`](get-proteins-transcripts.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/transcripts_proteins.ts`](../../src/routers/datatypeRouters/edges/transcripts_proteins.ts) |
| GET | [`/proteins/variants`](get-proteins-variants.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/variants_proteins.ts`](../../src/routers/datatypeRouters/edges/variants_proteins.ts) |

## /studies

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/studies`](get-studies.md) | ❌ AQL-only | [`src/routers/datatypeRouters/nodes/studies.ts`](../../src/routers/datatypeRouters/nodes/studies.ts) |

## /transcripts

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/transcripts`](get-transcripts.md) | ❌ AQL-only | [`src/routers/datatypeRouters/nodes/transcripts.ts`](../../src/routers/datatypeRouters/nodes/transcripts.ts) |
| GET | [`/transcripts/genes`](get-transcripts-genes.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/genes_transcripts.ts`](../../src/routers/datatypeRouters/edges/genes_transcripts.ts) |
| GET | [`/transcripts/proteins`](get-transcripts-proteins.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/transcripts_proteins.ts`](../../src/routers/datatypeRouters/edges/transcripts_proteins.ts) |

## /variants

| Method | Path | Status | Router |
|---|---|---|---|
| GET | [`/variants`](get-variants.md) | ✅ ClickHouse-ported | [`src/routers/datatypeRouters/nodes/variants.ts`](../../src/routers/datatypeRouters/nodes/variants.ts) |
| GET | [`/variants/biosamples`](get-variants-biosamples.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/variants_biosamples.ts`](../../src/routers/datatypeRouters/edges/variants_biosamples.ts) |
| GET | [`/variants/coding-variants`](get-variants-coding-variants.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/variants_coding_variants.ts`](../../src/routers/datatypeRouters/edges/variants_coding_variants.ts) |
| GET | [`/variants/diseases`](get-variants-diseases.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/variants_diseases.ts`](../../src/routers/datatypeRouters/edges/variants_diseases.ts) |
| GET | [`/variants/drugs`](get-variants-drugs.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/variants_drugs.ts`](../../src/routers/datatypeRouters/edges/variants_drugs.ts) |
| GET | [`/variants/freq`](get-variants-freq.md) | ✅ ClickHouse-ported | [`src/routers/datatypeRouters/nodes/variants.ts`](../../src/routers/datatypeRouters/nodes/variants.ts) |
| GET | [`/variants/genes`](get-variants-genes.md) | 🚧 Mixed | [`src/routers/datatypeRouters/edges/variants_genes.ts`](../../src/routers/datatypeRouters/edges/variants_genes.ts) |
| GET | [`/variants/genes-proteins`](get-variants-genes-proteins.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/genes_proteins_variants.ts`](../../src/routers/datatypeRouters/edges/genes_proteins_variants.ts) |
| GET | [`/variants/genes/summary`](get-variants-genes-summary.md) | 🚧 Mixed | [`src/routers/datatypeRouters/edges/variants_genes.ts`](../../src/routers/datatypeRouters/edges/variants_genes.ts) |
| GET | [`/variants/genomic-elements`](get-variants-genomic-elements.md) | 🚧 Mixed | [`src/routers/datatypeRouters/edges/variants_genomic_elements.ts`](../../src/routers/datatypeRouters/edges/variants_genomic_elements.ts) |
| GET | [`/variants/genomic-elements/cell-gene-predictions`](get-variants-genomic-elements-cell-gene-predictions.md) | 🚧 Mixed | [`src/routers/datatypeRouters/edges/variants_genomic_elements.ts`](../../src/routers/datatypeRouters/edges/variants_genomic_elements.ts) |
| GET | [`/variants/gnomad-alleles`](get-variants-gnomad-alleles.md) | ✅ ClickHouse-ported | [`src/routers/datatypeRouters/nodes/variants.ts`](../../src/routers/datatypeRouters/nodes/variants.ts) |
| GET | [`/variants/nearest-genes`](get-variants-nearest-genes.md) | 🚧 Mixed | [`src/routers/datatypeRouters/edges/variants_genes.ts`](../../src/routers/datatypeRouters/edges/variants_genes.ts) |
| GET | [`/variants/phenotypes`](get-variants-phenotypes.md) | ✅ ClickHouse-ported | [`src/routers/datatypeRouters/edges/variants_phenotypes.ts`](../../src/routers/datatypeRouters/edges/variants_phenotypes.ts) |
| GET | [`/variants/phenotypes/score-summary`](get-variants-phenotypes-score-summary.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/coding_variants_phenotypes.ts`](../../src/routers/datatypeRouters/edges/coding_variants_phenotypes.ts) |
| GET | [`/variants/predictions`](get-variants-predictions.md) | 🚧 Mixed | [`src/routers/datatypeRouters/edges/variants_genomic_elements.ts`](../../src/routers/datatypeRouters/edges/variants_genomic_elements.ts) |
| GET | [`/variants/predictions-count`](get-variants-predictions-count.md) | 🚧 Mixed | [`src/routers/datatypeRouters/edges/variants_genomic_elements.ts`](../../src/routers/datatypeRouters/edges/variants_genomic_elements.ts) |
| GET | [`/variants/proteins`](get-variants-proteins.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/variants_proteins.ts`](../../src/routers/datatypeRouters/edges/variants_proteins.ts) |
| GET | [`/variants/region-summary`](get-variants-region-summary.md) | ❓ Not in router files | _—_ |
| GET | [`/variants/summary`](get-variants-summary.md) | ✅ ClickHouse-ported | [`src/routers/datatypeRouters/nodes/variants.ts`](../../src/routers/datatypeRouters/nodes/variants.ts) |
| GET | [`/variants/variant-ld`](get-variants-variant-ld.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/variants_variants.ts`](../../src/routers/datatypeRouters/edges/variants_variants.ts) |
| GET | [`/variants/variant-ld/summary`](get-variants-variant-ld-summary.md) | ❌ AQL-only | [`src/routers/datatypeRouters/edges/variants_variants.ts`](../../src/routers/datatypeRouters/edges/variants_variants.ts) |
