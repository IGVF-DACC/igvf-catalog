# `cvp.variants` eliminates the VCV lookup for variant-linked phenotypes

Applies to the [`genes_coding_variants` router](../routers/genes_coding_variants.md).

`coding_variants_phenotypes` has a `variants` column that stores the linked genomic variant FK (`variants/NC_000013.11:...`) for assay types where the phenotype is tied to a specific nucleotide change (SGE, VAMP-seq). Extracting the variant ID directly from this column eliminates a separate `variants_coding_variants` lookup for those records, avoiding the need to touch the 1.56B-row VCV table at all for SGE data.

For protein-level phenotypes (MutPred2, ESM-1v), `cvp.variants` is empty. These still require a VCV lookup — see [gcv-04-vcv-projection.md](gcv-04-vcv-projection.md).
