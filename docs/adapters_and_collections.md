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
| GtexEQtl             | gtex_eqtl_adapter         | variants_genes                                          |
|                      |                           | variants_genes_terms                                    |
| CAQtl                | encode_caqtl_adapter      | regulatory_regions                                      |
|                      |                           | variants_regulatory_regions                             |
| CCRE                 | ccre_adapter              | regulatory_regions                                      |
| Ontology             | ontologies_adapter        | ontology_terms                                          |
| Uniprot              | uniprot_adapter           | transcripts_proteins                                    |
| UniprotProtein       | uniprot_protein_adapter   | proteins                                                |
| Favor                | favor_adapter             | variants                                                |
| ASB                  | adastra_asb_adapter       | variants_proteins                                       |
|                      |                           | variants_proteins_terms                                 |
| GtexSQtl             | gtex_sqtl_adapter         | variants_genes                                          |
|                      |                           | variants_genes_terms                                    |
|EncodeElementGeneLink |encode_element_gene_adapter| regulatory_regions_genes                                |
|                      |                           | regulatory_regions                                      |
|                      |                           | regulatory_regions_genes_biosamples                     |
|                      |                           | regulatory_regions_genes_biosamples_treatments_CHEBI    |
|                      |                           | regulatory_regions_genes_biosamples_treatments_proteins |
|                      |                           | regulatory_regions_genes_biosamples_donors              |
|                      |                           | donors                                                  |
|                      |                           | ontology_terms                                          |
| GAF                  | gaf_adapter               | go_terms_annotations                                    |
| GWAS                 | gwas_adapter              | studies                                                 |
|                      |                           | variants_phenotypes                                     |
|                      |                           | variants_phenotypes_studies                             |
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
| HumanMouseElementAdapter | human_mouse_element_adapter | mm_regulatory_regions                             |
|                      |                           | regulatory_regions                                      |
|                      |                           | regulatory_regions_mm_regulatory_regions                |
| EncodeMPRA           | encode_mpra_adapter       | regulatory_regions                                      |
|                      |                           | regulatory_regions_biosamples                           |
| MGIHumanMouseOrthologAdapter | mgi_human_mouse_ortholog_adapter | genes_mm_genes                           |
| ASB_GVATDB           | gvatdb_asb_adapter        | variants_proteins                                       |
| AFGREQtl             | AFGR_eqtl_adapter         | variants_genes                                          |
|                      |                           | variants_genes_terms                                    |
| AFGRSQtl             | AFGR_sqtl_adapter         | variants_genes                                          |
|                      |                           | variants_genes_terms                                    |
| AFGRCAQtl            | AFGR_caqtl_adapter        | regulatory_regions                                      |
|                      |                           | variants_regulatory_regions                             |
| DbSNFPAdapter        | dbSNFP_adapter            | coding_variants                                         |
| pQTL                 | pQTL_adapter              | variants_proteins                                       |
| GeneGeneBiogrid      | biogrid_gene_gene_adapter | genes_genes                                             |
|                      |                           | mm_genes_mm_genes                                       |
| ENCODE2GCRISPR       | encode_E2G_CRISPR_adapter | regulatory_region                                       |
|                      |                           | regulatory_regions_genes                                |
| MouseGenomesProjectAdapter | mouse_genomes_project_adapter| mm_variants                                    |
| ClinGen        | clingen_variant_disease_adapter | variants_diseases                                       |
|                      |                           | variants_diseases_genes                                 |
