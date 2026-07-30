# Adapters and Collections

Each adapter can write to several collections. Below is the table to display the relationship between adapters and collections.

| Adapter              | Module                    | Collection Name                                         |
|----------------------|---------------------------|---------------------------------------------------------|
| Gencode              | gencode_adapter           | transcripts                                             |
|                      |                           | mm_transcripts                                          |
|                      |                           | genes_transcripts                                       |
| GencodeGene          | gencode_gene_adapter      | genes                                                   |
|                      |                           | mm_genes                                                |
| TopLD                | topld_adapter             | variants_variants                                       |
| CAQtl                | encode_caqtl_adapter      | genomic_elements                                      |
|                      |                           | variants_genomic_elements                             |
| CCRE                 | ccre_adapter              | genomic_elements                                      |
| Ontology             | ontologies_adapter        | ontology_terms                                          |
|                      |                           | ontology_terms_ontology_terms                           |
| Favor                | favor_adapter             | variants                                                |
| ASB                  | adastra_asb_adapter       | variants_proteins                                       |
|EncodeElementGeneLink |encode_element_gene_adapter| genomic_elements_genes                                |
|                      |                           | genomic_elements                                      |
|                      |                           | genomic_elements_genes_biosamples                     |
|                      |                           | genomic_elements_genes_biosamples_treatments_CHEBI    |
|                      |                           | genomic_elements_genes_biosamples_treatments_proteins |
|                      |                           | genomic_elements_genes_biosamples_donors              |
|                      |                           | donors                                                  |
|                      |                           | ontology_terms                                          |
| GAF                  | gaf_adapter               | go_terms_annotations                                    |
| GWAS                 | gwas_adapter              | studies                                                 |
|                      |                           | variants_phenotypes                                     |
| Motif                | motif_adapter             | motifs                                                  |
|                      |                           | motifs_proteins                                         |
| Coxpresdb            | coxpresdb_adapter         | genes_genes                                             |
| ReactomePathway      | reactome_pathway_adapter  | pathways                                                |
| Reactome             | reactome_adapter          | genes_pathways                                          |
|                      |                           | pathways_pathways                                       |
| Cellosaurus         |cellosaurus_ontology_adapter| ontology_terms                                          |
|                      |                           | ontology_terms_ontology_terms                           |
| PharmGKB             | pharmgkb_drug_adapter     | drugs                                                   |
|                      |                           | variants_drugs                                          |
|                      |                           | variants_drugs_genes                                    |
| Disease              | orphanet_disease_adapter  | diseases_genes                                          |
| Oncotree             | oncotree_adapter          | ontology_terms                                          |
|                      |                           | ontology_terms_ontology_terms                           |
| DepMap               | depmap_adapter            | genes_terms                                             |
| EBIComplex           | ebi_complex_adapter       | complexes                                               |
|                      |                           | complexes_proteins                                      |
|                      |                           | complexes_terms                                         |
| ProteinsInteraction  | proteins_interaction_adapter | proteins_proteins                                    |
| HumanMouseElementAdapter | human_mouse_element_adapter | mm_genomic_elements                             |
|                      |                           | genomic_elements                                      |
|                      |                           | genomic_elements_mm_genomic_elements                |
| EncodeMPRA           | encode_mpra_adapter       | genomic_elements                                      |
|                      |                           | genomic_elements_biosamples                           |
| MGIHumanMouseOrthologAdapter | mgi_human_mouse_ortholog_adapter | genes_mm_genes                           |
| ASB_GVATDB           | gvatdb_asb_adapter        | variants_proteins                                       |
| AFGREQtl             | AFGR_eqtl_adapter         | variants_genes                                          |
| AFGRSQtl             | AFGR_sqtl_adapter         | variants_genes                                          |
| AFGRCAQtl            | AFGR_caqtl_adapter        | genomic_elements                                      |
|                      |                           | variants_genomic_elements                             |
| DbSNFPAdapter        | dbSNFP_adapter            | coding_variants                                         |
|                      |                           | variants_coding_variants                                |
| pQTL                 | pQTL_adapter              | variants_proteins                                       |
| GeneGeneBiogrid      | biogrid_gene_gene_adapter | genes_genes                                             |
|                      |                           | mm_genes_mm_genes                                       |
| CRISPRElementGeneENCODE | CRISPR_element_gene_ENCODE_adapter | genomic_elements                               |
|                      |                           | genomic_elements_genes                                  |
| CRISPRElementGeneIGVF | CRISPR_element_gene_IGVF_adapter | genomic_elements                                    |
|                      |                           | genomic_elements_genes                                  |
| CRISPRElementPhenotype | CRISPR_element_phenotype_adapter | genomic_elements                                  |
|                      |                           | genomic_elements_phenotypes                             |
| CRISPRVariantGene    | CRISPR_variant_gene_adapter | variants                                              |
|                      |                           | variants_genes                                          |
| CRISPRVariantPhenotype | CRISPR_variant_phenotype_adapter | variants                                          |
|                      |                           | variants_phenotypes                                     |
|                      |                           | ontology_terms                                          |
| MouseGenomesProjectAdapter | mouse_genomes_project_adapter| mm_variants                                    |
| ClinGen        | clingen_variant_disease_adapter | variants_diseases                                       |
|                      |                           | variants_diseases_genes                                 |
