# Collection Key

The schema for each collecion we load into our database is defined in data/schemas. But the key definition for each collection is not defined in schema. We will document the key definition in this document.

| Model                                             | Type | Collection name                     | Hashed | Key format | Example |
| :------------------------------------------------ | ---: | ----------------------------------: | -----: | ---------: | ----: |
| accessible dna element                             | node | regulatory_regions              | N | accessible_dna_element_{chr}\_{start}\_{end}\_{assembly} | chr1_778381_779150_GRCh38 |
| ccre regulatory region                            | node | regulatory_regions   | N | {candidate_cis_regulatory_element_id} | EH38E2776516 |
| gene                                              | node | genes                               | N | {Ensembl_id}{optinal suffix _PAR_Y} | ENSG00000197976 or ENSG00000197976_PAR_Y|
| ontology term                                     | node | ontology_terms                      | N | {ontology}_{id} | EFO_0001086 |
| protein                                           | node | proteins                            | N | {Uniprot_id} | P31946 |
| pathway                                           | node | pathways                            | N | {reactome_id} | R-HSA-109581 |
| regulatory region                                 | node | regulatory_regions                  | N | {class_name}\_{chr}\_{start}\_{end}\_{assembly} | enhancer_chr1_827140_827667_GRCh38 |
| transcript                                        | node | transcripts                         | N |  {Ensembl_id}{optinal suffix _PAR_Y} | ENST00000313871 or ENST00000313871_PAR_Y |
| sequence variant                                  | node | variants                            | Y | {chr}_{start}\_{ref_seq}\_{alt_seq}\_{assembly} | 20_9567040_T_G_GRCh38 |
| allele specific binding   | edge | variants_proteins               | N | {variant_id}\_{uniprot_id}|
| allele specific binding cell ontology   | edge | variants_proteins_terms |  N  | {variant_id}\_{uniprot_id}\_{cell_name} |
| variant to protein association   |  edge  |  variants_proteins  |  N  |  {variant_id}\_{uniprot_id}\_{source}  |  45680fb8f0bb29a0f0d19fa5fa73eb603d15956b841bc3813ad6f5ecc5c3039d_P09110_UKB |
| child pathway of                                 | edge | pathways_pathways                   | N | {pathway_id}_{pathway_id} | R-HSA-109581_R-HSA-109606 |
| gaf                                               | edge | go_gene_product_links               | Y | {annotation_dict}  |
| gene to pathway association                       | edge | genes_pathways                      | N | {gene_id}_{pathway_id} | ENSG00000000419_R-HSA-162699 |
| studies       | node | studies                  | N | {study_id} |
| studies to variants       | edge | studies_variants                  | Y | {study_id}\_{variant_id} |
| study variant association to phenotype       | edge | studies_variants_phenotypes                  | Y | {study_id}\_{variant_id}\_{ontology_term_id} |
| ontology relationship                             | edge | ontology_relationships              | N | {from_node}\_{predicate}\_{to_node} | obo:GO_0000001_01:rdf-schema.subClassOf_obo:GO_0048308 |
| parent pathway of                                 | edge | pathways_pathways                   | N | {pathway_id}_{pathway_id} | R-HSA-109581_R-HSA-109606 |
| regulatory element to gene expression association | edge | regulatory_regions_genes                      | N | {regulatory_region_id}_{gene id}_{file_accesion} | enhancer_chr1_827140_827667_GRCh38_ENSG00000187634_ENCFF712SUP |
| regulatory element to gene expression association to biosample | edge | regulatory_regions_genes_biosamples  | N | {regulatory_region_id}_{gene id}_{file_accesion}_{biosample_ontology_term_id} | promoter_chr1_778390_779142_GRCh38_ENSG00000225880_ENCFF617FJH_EFO_0001203 |
| regulatory element to gene expression association to biosample to CHEBI treatment | edge | regulatory_regions_genes_biosamples_treatments_CHEBI | N | {regulatory_region_id}_{gene id}_{file_accesion}_{treatment_ontology_term_id} | promoter_chr1_778390_779142_GRCh38_ENSG00000225880_ENCFF617FJH_CHEBI_23965 |
| regulatory element to gene expression association to biosample to protein treatment | edge | regulatory_regions_genes_biosamples_treatments_proteins | N | {regulatory_region_id}_{gene id}_{file_accesion}_{treatment_protein_id} | intergenic_chr1_633776_634276_GRCh38_ENSG00000225880_ENCFF728HSS_P60568 |
| regulatory element to gene expression association to biosample to donor | edge | regulatory_regions_genes_biosamples_donors | N | {regulatory_region_id}_{gene id}_{file_accesion}_{donor_id} | promoter_chr1_827209_827840_GRCh38_ENSG00000225880_ENCFF617FJH_ENCDO000AAE |
| donor |    node |  donors |  N | {donor_id} | ENCDO000AAE|
| topld in linkage disequilibrium with              | edge | variant_correlations                | Y | {ancestry}{chr}{uniq_id_snp1}{uniq_id_snp2}{assembly}|
| regulatory element to biosample  | edge |  regulatory_regions_biosamples  | N  | {regulatory_region_id}\_{file_accesion}\_{biosample_ontology_term_id}  |   MPRA_chr1_632980_633180_GRCh38_ENCFF802FUV_EFO_0002067
 |
| transcribed from                                  | edge | gencode_transcripts                 | N | {transcript_id}_{gene_id} | ENST00000456328_ENSG00000290825 |
| transcribed to                                    | edge | gencode_transcripts                 | N | {gene_id}_{transcript_id} | ENSG00000290825_ENST00000456328 |
| translates to                                     | edge | protein_transcript_relationship     | N | {protein_id}_{transcript_id} | P31946_ENST00000353703 |
| translation of                                    | edge | protein_transcript_relationship     | N | {transcript_id}_{protein_id} | ENST00000353703_P31946 |
| variant to regulatory region      | edge | variant_accessible_dna_region_links | N | {variant_id}_{regulatory_region_id} |
| drugs      | node | drugs | N | {drug_id} | PA166178620  |
| variant to drug      | edge | variants_drugs | N | {variantAnnotation_id}_{drug_id} | 608178486_PA450657 |
| variant drug association to gene    | edge   | variants_drugs_genes  | N | {variantAnnotation_id}\_{drug_id}\_{gene_id}   |  608178486_PA450657_ENSG00000085563  |
| disease to gene                   | edge | diseases_genes     | N | {ontology_term_id}_{gene_id}   | Orphanet_93_ENSG00000038002  |
| gene to term         | edge | genes_terms    | N | {gene_id}_{ontology_term_id} | ENSG00000117362_CVCL_A1VE   |
| complex   | node  | complexes | N | {complex_id}  |   CPX-1  |
| complex to protein |  edge  |  complexes_proteins  | N |  {complex_id}_{protein_id} | CPX-1_Q15796  |
| complex to term |  edge  |   complexes_terms  | N  |  {complex_id}_{ontology_term_id}  |  CPX-1_GO_0006355  |
| protein to protein  | edge | proteins_proteins   | N | {protein_id}_{protein_id}_{detection_method_code}_{pmids} | A5YKK6_Q9UPQ9_MI_0096_21981923
