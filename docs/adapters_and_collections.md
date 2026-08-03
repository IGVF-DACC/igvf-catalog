# Adapters and Collections

Each adapter can write to several collections. The collection an adapter writes to
is either taken directly from its `label` or resolved from the `label` (and, in a few
cases, other inputs) by the adapter's `_get_collection_name()` method. The table below
lists that relationship for every adapter registered in `data/active_adapters.py`.

The collection names were derived from each adapter's `_get_collection_name()` (or, for
the non-`BaseAdapter` adapters `Ontology`, `Oncotree`, and `FileFileSet`, from their
writer/validation logic) and cross-checked against the canonical node/edge collection
registry in `data/schemas/registry.json`.

| Adapter                      | Module                              | Collection Name(s)                                                                          |
|------------------------------|-------------------------------------|--------------------------------------------------------------------------------------------|
| Gencode                      | gencode_adapter                     | transcripts<br>mm_transcripts<br>genes_transcripts                                          |
| GencodeGene                  | gencode_gene_adapter                | genes<br>mm_genes                                                                           |
| GencodeProtein               | gencode_protein_adapter             | proteins<br>transcripts_proteins                                                            |
| GencodeStructure             | gencode_gene_structure_adapter      | genes_structure<br>mm_genes_structure<br>transcripts_genes_structure<br>mm_transcripts_mm_genes_structure |
| TopLD                        | topld_adapter                       | variants_variants                                                                           |
| CAQtl                        | encode_caqtl_adapter                | genomic_elements<br>variants_genomic_elements                                              |
| CCRE                         | ccre_adapter                        | genomic_elements<br>mm_genomic_elements                                                     |
| Ontology                     | ontologies_adapter                  | ontology_terms<br>ontology_terms_ontology_terms                                             |
| Favor                        | favor_adapter                       | variants                                                                                    |
| ASB                          | adastra_asb_adapter                 | variants_proteins                                                                           |
| EncodeElementGeneLink        | encode_element_gene_adapter         | genomic_elements<br>genomic_elements_genes                                                  |
| GAF                          | gaf_adapter                         | gene_products_terms                                                                         |
| GWAS                         | gwas_adapter                        | studies<br>variants_phenotypes                                                              |
| Motif                        | motif_adapter                       | motifs<br>motifs_proteins                                                                   |
| Coxpresdb                    | coxpresdb_adapter                   | genes_genes                                                                                 |
| ReactomePathway              | reactome_pathway_adapter            | pathways                                                                                    |
| Reactome                     | reactome_adapter                    | genes_pathways<br>pathways_pathways                                                         |
| Cellosaurus                  | cellosaurus_ontology_adapter        | ontology_terms<br>ontology_terms_ontology_terms                                             |
| PharmGKB                     | pharmgkb_drug_adapter               | drugs<br>variants_drugs<br>variants_drugs_genes                                             |
| Disease                      | orphanet_disease_adapter            | diseases_genes                                                                              |
| Oncotree                     | oncotree_adapter                    | ontology_terms<br>ontology_terms_ontology_terms                                             |
| DepMap                       | depmap_adapter                      | genes_biosamples                                                                            |
| EBIComplex                   | ebi_complex_adapter                 | complexes<br>complexes_proteins<br>complexes_terms                                          |
| ProteinsInteraction          | proteins_interaction_adapter        | proteins_proteins                                                                           |
| HumanMouseElementAdapter     | human_mouse_element_adapter         | genomic_elements<br>mm_genomic_elements<br>genomic_elements_mm_genomic_elements            |
| MPRAAdapter                  | mpra_adapter                        | variants<br>variants_biosamples<br>genomic_elements<br>genomic_elements_biosamples         |
| MGIHumanMouseOrthologAdapter | mgi_human_mouse_ortholog_adapter    | genes_mm_genes                                                                              |
| ASB_GVATDB                   | gvatdb_asb_adapter                  | variants_proteins                                                                           |
| AFGREQtl                     | AFGR_eqtl_adapter                   | variants_genes                                                                              |
| AFGRSQtl                     | AFGR_sqtl_adapter                   | variants_genes                                                                              |
| AFGRCAQtl                    | AFGR_caqtl_adapter                  | genomic_elements<br>variants_genomic_elements                                              |
| DbNSFP                       | dbNSFP_adapter                      | coding_variants<br>variants_coding_variants<br>coding_variants_proteins                     |
| pQTL                         | pQTL_adapter                        | variants_proteins                                                                           |
| GeneGeneBiogrid              | biogrid_gene_gene_adapter           | genes_genes<br>mm_genes_mm_genes                                                            |
| CRISPRElementGeneENCODE      | CRISPR_element_gene_ENCODE_adapter  | genomic_elements<br>genomic_elements_genes                                                  |
| CRISPRElementGeneIGVF        | CRISPR_element_gene_IGVF_adapter    | genomic_elements<br>genomic_elements_genes                                                  |
| CRISPRElementPhenotype       | CRISPR_element_phenotype_adapter    | genomic_elements<br>genomic_elements_phenotypes                                             |
| CRISPRVariantPhenotype       | CRISPR_variant_phenotype_adapter    | variants<br>ontology_terms<br>variants_phenotypes                                           |
| CRISPRVariantGene            | CRISPR_variant_gene_adapter         | variants<br>variants_genes                                                                  |
| MouseGenomesProjectAdapter   | mouse_genomes_project_adapter       | mm_variants                                                                                 |
| ClinGen                      | clingen_variant_disease_adapter     | variants_diseases<br>variants_diseases_genes                                                |
| VAMPAdapter                  | VAMP_coding_variant_scores_adapter  | coding_variants_phenotypes                                                                  |
| SEMMotif                     | SEM_motif_adapter                   | motifs<br>motifs_proteins<br>complexes<br>complexes_proteins                                |
| SEMPred                      | SEM_prediction_adapter              | variants_proteins                                                                           |
| BlueSTARRVariantBiosample    | BlueSTARR_variants_biosamples_adapter | variants<br>variants_biosamples                                                           |
| STARRseqVariantBiosample     | STARR_seq_adapter                   | variants<br>variants_biosamples                                                             |
| FileFileSet                  | file_fileset_adapter                | files_filesets<br>donors<br>ontology_terms                                                  |
| EQTLCatalog                  | eqtl_catalog_adapter                | variants_genes<br>studies                                                                   |
| SGE                          | SGE_variant_phenotype_adapter       | variants<br>variants_phenotypes<br>coding_variants_phenotypes                               |
| cV2F                         | cV2F_variant_phenotype_adapter      | variants<br>variants_phenotypes                                                             |
| Mutpred2CodingVariantsScores | Mutpred2_coding_variants_adapter    | coding_variants<br>variants<br>variants_coding_variants<br>coding_variants_phenotypes       |
| ESM1vCodingVariantsScores    | ESM_coding_variants_adapter         | coding_variants<br>variants<br>variants_coding_variants<br>coding_variants_phenotypes       |
| GenccDiseasesGenes           | gencc_diseases_genes_adapter        | diseases_genes                                                                              |
| scE2G                        | scE2G_adapter                       | genomic_elements<br>genomic_elements_genes                                                  |
| DUALIPAAdapter               | DUAL_IPA_coding_variant_scores_adapter | coding_variants_phenotypes                                                               |
