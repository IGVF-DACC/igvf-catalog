# Collection Keys

Every document in the catalog is identified by `_key`, unique within its collection. The key
composition for each collection is documented in the `_key` description of that collection's
schema under `data/schemas`; this page explains the conventions those keys follow.

Previously this page carried the per-collection key formats because they were not recorded in the
schemas. They now are, so the formats live in the schemas and this page no longer duplicates them.

## Conventions

Keys are built one of three ways.

**Source accession.** Where the upstream source already issues a stable identifier, that identifier
is the key, with version suffixes stripped and characters that ArangoDB disallows rewritten. Ensembl
IDs drop the version (`ENSG00000197976.12` becomes `ENSG00000197976`) and take a `_PAR_Y` suffix for
the pseudoautosomal copy on chromosome Y. Ontology term IDs replace the colon with an underscore, so
`EFO:0001086` becomes `EFO_0001086`.

**Composite.** Where no single accession identifies the record, the key is the underscore-joined
concatenation of the fields that make it unique. Genomic elements use
`{class}_{chr}_{start}_{end}_{assembly}`, and edges typically append the endpoints plus the accession
of the source file, which is what distinguishes two measurements of the same relationship reported by
different experiments.

**Hashed.** ArangoDB limits `_key` to 254 characters, so adapters fall back to a SHA-256 hex digest
when a composite would exceed that. Some collections always hash. Two consequences are worth knowing:
a hashed key is not parseable back into its parts, and variant keys switch representation at the
length boundary — a variant is keyed by its SPDI expression, or by its GA4GH VRS allele digest when
the SPDI is too long.

## Variant keys

Variants are keyed by the normalized SPDI expression, for example `NC_000001.11:10202:C:A`, which is
also stored in `spdi` and used as the `name`. SPDI uses a RefSeq accession, a 0-based position, the
deleted sequence and the inserted sequence. Coding variants are keyed as
`{gene_name}_{transcript_id}_{protein_hgvs}_{coding_hgvs}`, for example
`OR4F5_ENST00000641515_p.Met1!_c.1A-C`; note that `?` is rewritten to `!` and `>` to `-`.

## Collections

The catalog has 54 collections, loaded by the adapter and schema pairs below. Where several adapters
write into one collection, each has its own schema and its own key composition.

| Collection | Type | Adapter | Schema |
| :--- | :--- | :--- | :--- |
| `coding_variants_phenotypes` | edge | `DUALIPAAdapter` | `edges/coding_variants_phenotypes.DUALIPAAdapter.json` |
| `coding_variants_phenotypes` | edge | `ESM1vCodingVariantsScores` | `edges/coding_variants_phenotypes.ESM1vCodingVariantsScores.json` |
| `coding_variants_phenotypes` | edge | `Mutpred2CodingVariantsScores` | `edges/coding_variants_phenotypes.Mutpred2CodingVariantsScores.json` |
| `coding_variants_phenotypes` | edge | `SGE` | `edges/coding_variants_phenotypes.SGE.json` |
| `coding_variants_phenotypes` | edge | `VAMPAdapter` | `edges/coding_variants_phenotypes.VAMPAdapter.json` |
| `coding_variants_phenotypes` | edge | `VariantPaintingAdapter` | `edges/coding_variants_phenotypes.VariantPaintingAdapter.json` |
| `coding_variants_proteins` | edge | `DbNSFP` | `edges/coding_variants_proteins.DbNSFP.json` |
| `complexes_proteins` | edge | `EBIComplex` | `edges/complexes_proteins.EBIComplex.json` |
| `complexes_proteins` | edge | `SEMMotif` | `edges/complexes_proteins.SEMMotif.json` |
| `complexes_terms` | edge | `EBIComplex` | `edges/complexes_terms.EBIComplex.json` |
| `diseases_genes` | edge | `Disease` | `edges/diseases_genes.Disease.json` |
| `diseases_genes` | edge | `GenccDiseasesGenes` | `edges/diseases_genes.GenccDiseasesGenes.json` |
| `gene_products_terms` | edge | `GAF` | `edges/gene_products_terms.GAF.json` |
| `genes_biosamples` | edge | `DepMap` | `edges/genes_biosamples.DepMap.json` |
| `genes_genes` | edge | `Coxpresdb` | `edges/genes_genes.Coxpresdb.json` |
| `genes_genes` | edge | `GeneGeneBiogrid` | `edges/genes_genes.GeneGeneBiogrid.json` |
| `genes_mm_genes` | edge | `MGIHumanMouseOrthologAdapter` | `edges/genes_mm_genes.MGIHumanMouseOrthologAdapter.json` |
| `genes_pathways` | edge | `Reactome` | `edges/genes_pathways.Reactome.json` |
| `genes_transcripts` | edge | `Gencode` | `edges/genes_transcripts.Gencode.json` |
| `genomic_elements_biosamples` | edge | `MPRAAdapter` | `edges/genomic_elements_biosamples.MPRAAdapter.json` |
| `genomic_elements_genes` | edge | `CRISPRElementGeneENCODE` | `edges/genomic_elements_genes.CRISPRElementGeneENCODE.json` |
| `genomic_elements_genes` | edge | `CRISPRElementGeneIGVF` | `edges/genomic_elements_genes.CRISPRElementGeneIGVF.json` |
| `genomic_elements_genes` | edge | `EncodeElementGeneLink` | `edges/genomic_elements_genes.EncodeElementGeneLink.json` |
| `genomic_elements_genes` | edge | `scE2G` | `edges/genomic_elements_genes.scE2G.json` |
| `genomic_elements_mm_genomic_elements` | edge | `HumanMouseElementAdapter` | `edges/genomic_elements_mm_genomic_elements.HumanMouseElementAdapter.json` |
| `genomic_elements_phenotypes` | edge | `CRISPRElementPhenotype` | `edges/genomic_elements_phenotypes.CRISPRElementPhenotype.json` |
| `mm_genes_mm_genes` | edge | `GeneGeneBiogrid` | `edges/mm_genes_mm_genes.GeneGeneBiogrid.json` |
| `mm_transcripts_mm_genes_structure` | edge | `GencodeStructure` | `edges/mm_transcripts_mm_genes_structure.GencodeStructure.json` |
| `motifs_proteins` | edge | `Motif` | `edges/motifs_proteins.Motif.json` |
| `motifs_proteins` | edge | `SEMMotif` | `edges/motifs_proteins.SEMMotif.json` |
| `ontology_terms_ontology_terms` | edge | `Cellosaurus` | `edges/ontology_terms_ontology_terms.Cellosaurus.json` |
| `ontology_terms_ontology_terms` | edge | `Oncotree` | `edges/ontology_terms_ontology_terms.Oncotree.json` |
| `ontology_terms_ontology_terms` | edge | `Ontology` | `edges/ontology_terms_ontology_terms.Ontology.json` |
| `pathways_pathways` | edge | `Reactome` | `edges/pathways_pathways.Reactome.json` |
| `proteins_proteins` | edge | `ProteinsInteraction` | `edges/proteins_proteins.ProteinsInteraction.json` |
| `transcripts_genes_structure` | edge | `GencodeStructure` | `edges/transcripts_genes_structure.GencodeStructure.json` |
| `transcripts_proteins` | edge | `GencodeProtein` | `edges/transcripts_proteins.GencodeProtein.json` |
| `variants_biosamples` | edge | `BlueSTARRVariantBiosample` | `edges/variants_biosamples.BlueSTARRVariantBiosample.json` |
| `variants_biosamples` | edge | `MPRAAdapter` | `edges/variants_biosamples.MPRAAdapter.json` |
| `variants_biosamples` | edge | `STARRseqVariantBiosample` | `edges/variants_biosamples.STARRseqVariantBiosample.json` |
| `variants_coding_variants` | edge | `DbNSFP` | `edges/variants_coding_variants.DbNSFP.json` |
| `variants_coding_variants` | edge | `ESM1vCodingVariantsScores` | `edges/variants_coding_variants.ESM1vCodingVariantsScores.json` |
| `variants_coding_variants` | edge | `Mutpred2CodingVariantsScores` | `edges/variants_coding_variants.Mutpred2CodingVariantsScores.json` |
| `variants_diseases` | edge | `ClinGen` | `edges/variants_diseases.ClinGen.json` |
| `variants_diseases_genes` | edge | `ClinGen` | `edges/variants_diseases_genes.ClinGen.json` |
| `variants_drugs` | edge | `PharmGKB` | `edges/variants_drugs.PharmGKB.json` |
| `variants_drugs_genes` | edge | `PharmGKB` | `edges/variants_drugs_genes.PharmGKB.json` |
| `variants_genes` | edge | `AFGREQtl` | `edges/variants_genes.AFGREQtl.json` |
| `variants_genes` | edge | `AFGRSQtl` | `edges/variants_genes.AFGRSQtl.json` |
| `variants_genes` | edge | `CRISPRVariantGene` | `edges/variants_genes.CRISPRVariantGene.json` |
| `variants_genes` | edge | `EQTLCatalog` | `edges/variants_genes.EQTLCatalog.json` |
| `variants_genomic_elements` | edge | `AFGRCAQtl` | `edges/variants_genomic_elements.AFGRCAQtl.json` |
| `variants_genomic_elements` | edge | `CAQtl` | `edges/variants_genomic_elements.CAQtl.json` |
| `variants_phenotypes` | edge | `CRISPRVariantPhenotype` | `edges/variants_phenotypes.CRISPRVariantPhenotype.json` |
| `variants_phenotypes` | edge | `GWAS` | `edges/variants_phenotypes.GWAS.json` |
| `variants_phenotypes` | edge | `SGE` | `edges/variants_phenotypes.SGE.json` |
| `variants_phenotypes` | edge | `cV2F` | `edges/variants_phenotypes.cV2F.json` |
| `variants_proteins` | edge | `ASB` | `edges/variants_proteins.ASB.json` |
| `variants_proteins` | edge | `ASB_GVATDB` | `edges/variants_proteins.ASB_GVATDB.json` |
| `variants_proteins` | edge | `SEMPred` | `edges/variants_proteins.SEMPred.json` |
| `variants_proteins` | edge | `pQTL` | `edges/variants_proteins.pQTL.json` |
| `variants_variants` | edge | `TopLD` | `edges/variants_variants.TopLD.json` |
| `coding_variants` | node | `DbNSFP` | `nodes/coding_variants.DbNSFP.json` |
| `coding_variants` | node | `ESM1vCodingVariantsScores` | `nodes/coding_variants.ESM1vCodingVariantsScores.json` |
| `coding_variants` | node | `Mutpred2CodingVariantsScores` | `nodes/coding_variants.Mutpred2CodingVariantsScores.json` |
| `complexes` | node | `EBIComplex` | `nodes/complexes.EBIComplex.json` |
| `complexes` | node | `SEMMotif` | `nodes/complexes.SEMMotif.json` |
| `donors` | node | `FileFileSet` | `nodes/donors.FileFileSet.json` |
| `drugs` | node | `PharmGKB` | `nodes/drugs.PharmGKB.json` |
| `files_filesets` | node | `FileFileSet` | `nodes/files_filesets.FileFileSet.json` |
| `genes` | node | `GencodeGene` | `nodes/genes.GencodeGene.json` |
| `genes_structure` | node | `GencodeStructure` | `nodes/genes_structure.GencodeStructure.json` |
| `genomic_elements` | node | `AFGRCAQtl` | `nodes/genomic_elements.AFGRCAQtl.json` |
| `genomic_elements` | node | `CAQtl` | `nodes/genomic_elements.CAQtl.json` |
| `genomic_elements` | node | `CCRE` | `nodes/genomic_elements.CCRE.json` |
| `genomic_elements` | node | `CRISPRElementGeneENCODE` | `nodes/genomic_elements.CRISPRElementGeneENCODE.json` |
| `genomic_elements` | node | `CRISPRElementGeneIGVF` | `nodes/genomic_elements.CRISPRElementGeneIGVF.json` |
| `genomic_elements` | node | `CRISPRElementPhenotype` | `nodes/genomic_elements.CRISPRElementPhenotype.json` |
| `genomic_elements` | node | `EncodeElementGeneLink` | `nodes/genomic_elements.EncodeElementGeneLink.json` |
| `genomic_elements` | node | `HumanMouseElementAdapter` | `nodes/genomic_elements.HumanMouseElementAdapter.json` |
| `genomic_elements` | node | `MPRAAdapter` | `nodes/genomic_elements.MPRAAdapter.json` |
| `genomic_elements` | node | `scE2G` | `nodes/genomic_elements.scE2G.json` |
| `mm_genes` | node | `GencodeGene` | `nodes/mm_genes.GencodeGene.json` |
| `mm_genes_structure` | node | `GencodeStructure` | `nodes/mm_genes_structure.GencodeStructure.json` |
| `mm_genomic_elements` | node | `CCRE` | `nodes/mm_genomic_elements.CCRE.json` |
| `mm_genomic_elements` | node | `HumanMouseElementAdapter` | `nodes/mm_genomic_elements.HumanMouseElementAdapter.json` |
| `mm_transcripts` | node | `Gencode` | `nodes/mm_transcripts.Gencode.json` |
| `mm_variants` | node | `MouseGenomesProjectAdapter` | `nodes/mm_variants.MouseGenomesProjectAdapter.json` |
| `motifs` | node | `Motif` | `nodes/motifs.Motif.json` |
| `motifs` | node | `SEMMotif` | `nodes/motifs.SEMMotif.json` |
| `ontology_terms` | node | `CRISPRVariantPhenotype` | `nodes/ontology_terms.CRISPRVariantPhenotype.json` |
| `ontology_terms` | node | `Cellosaurus` | `nodes/ontology_terms.Cellosaurus.json` |
| `ontology_terms` | node | `FileFileSet` | `nodes/ontology_terms.FileFileSet.json` |
| `ontology_terms` | node | `Oncotree` | `nodes/ontology_terms.Oncotree.json` |
| `ontology_terms` | node | `Ontology` | `nodes/ontology_terms.Ontology.json` |
| `pathways` | node | `ReactomePathway` | `nodes/pathways.ReactomePathway.json` |
| `proteins` | node | `GencodeProtein` | `nodes/proteins.GencodeProtein.json` |
| `studies` | node | `EQTLCatalog` | `nodes/studies.EQTLCatalog.json` |
| `studies` | node | `GWAS` | `nodes/studies.GWAS.json` |
| `transcripts` | node | `Gencode` | `nodes/transcripts.Gencode.json` |
| `variants` | node | `BlueSTARRVariantBiosample` | `nodes/variants.BlueSTARRVariantBiosample.json` |
| `variants` | node | `CRISPRVariantGene` | `nodes/variants.CRISPRVariantGene.json` |
| `variants` | node | `CRISPRVariantPhenotype` | `nodes/variants.CRISPRVariantPhenotype.json` |
| `variants` | node | `ESM1vCodingVariantsScores` | `nodes/variants.ESM1vCodingVariantsScores.json` |
| `variants` | node | `Favor` | `nodes/variants.Favor.json` |
| `variants` | node | `MPRAAdapter` | `nodes/variants.MPRAAdapter.json` |
| `variants` | node | `Mutpred2CodingVariantsScores` | `nodes/variants.Mutpred2CodingVariantsScores.json` |
| `variants` | node | `SGE` | `nodes/variants.SGE.json` |
| `variants` | node | `STARRseqVariantBiosample` | `nodes/variants.STARRseqVariantBiosample.json` |
| `variants` | node | `autogenerated_topld` | `nodes/variants.autogenerated_topld.json` |
| `variants` | node | `cV2F` | `nodes/variants.cV2F.json` |
