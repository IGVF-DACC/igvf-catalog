export const descriptions = {
  regulatory_regions: 'Retrieve regulatory regions.<br> Example: region = chr1:1157520-1158189, biochemical_activity = CA, source = ENCODE_SCREEN (ccREs). The limit parameter controls the page size and can not exceed 1000.',
  regulatory_regions_genes: 'Retrieve regulatory region and gene pairs by querying regulatory regions.<br> \
  Region is required. Example region = chr1:903900-904900;  biochemical_activity = ENH. <br> <br> \
  Filters on source, region_type and biochemical_activity work only in specific combinations based on data availability. <br> \
  For example: <br> \
  1. source = ENCODE_EpiRaction, region_type = candidate_cis_regulatory_element; biochemical_activity = ENH (i.e. enhancer). <br> \
  2. source = ENCODE-E2G-DNaseOnly and ENCODE-E2G-Full, region_type = candidate_cis_regulatory_element; biochemical_activity = ENH or PRO (i.e. promoter). <br> \
  3. source = ENCODE-E2G-CRISPR, region_type = enhancer  or CRISPR_tested_element [Note: the enhancers list includes all elements that were found to be positive (with significant = True) for any tested gene while the CRISPR_tested_element lists all the elements ever tested but found to be negative (with significant = False) for all tested genes] ; biochemical_activity = ENH (positive cases) or Null (negative cases). <br> <br>\
  Set verbose = true to retrieve full info on the regulatory regions.<br>The limit parameter controls the page size and can not exceed 500.',
  genes_regulatory_regions: 'Retrieve regulatory region - gene pairs by querying genes.<br> \
  Set verbose = true to retrieve full info on the genes.<br> Example: gene_id = ENSG00000187634, gene_name = SAMD11, region = chr1:923900-924900<br>The limit parameter controls the page size and can not exceed 500.',
  genes: 'Retrieve genes.<br> Example: name = SAMD1, gene_region = chr1:212565300-212620800, alias = CKLF, gene_id = ENSG00000187642 (Ensembl ids)<br>The limit parameter controls the page size and can not exceed 500.',
  transcripts: 'Retrieve transcripts.<br> Example: region = chr20:9537369-9839076, transcript_type = protein_coding, id = ENST00000443707 (Ensembl ids)<br>The limit parameter controls the page size and can not exceed 500.',
  proteins: 'Retrieve proteins.<br> Example: name = 1433B_HUMAN, dbxrefs = ENSP00000494538.1, protein_id = P49711 (Uniprot ids)<br>The limit parameter controls the page size and can not exceed 50.',
  genes_transcripts: 'Retrieve transcripts from genes.<br> \
    Set verbose = true to retrieve full info on the transcripts.<br> Example: gene_name = ATF3, gene_region = chr1:212565300-212620800, alias = CKLF, gene_id = ENSG00000187642 (Ensembl ids)<br>The limit parameter controls the page size and can not exceed 100.',
  transcripts_genes: 'Retrieve genes from transcripts.<br> \
    Set verbose = true to retrieve full info on the genes.<br> Example: region = chr1:711800-740000, transcript_id = ENST00000443707 (Ensembl ID)<br>The limit parameter controls the page size and can not exceed 100.',
  genes_proteins: 'Retrieve proteins from genes.<br>Set verbose = true to retrieve full info on the proteins. \
  <br> Example: gene_name = ATF3, gene_region = chr1:212565300-212620800, alias = CKLF, gene_id = ENSG00000170558 (Ensembl ID)<br>The limit parameter controls the page size and can not exceed 100.',
  proteins_genes: 'Retrieve genes from proteins.<br> \
  Set verbose = true to retrieve full info on the genes.<br> Example: protein_name = CTCF_HUMAN, dbxrefs = HGNC:13723, protein_id = P49711<br>The limit parameter controls the page size and can not exceed 100.',
  transcripts_proteins: 'Retrieve proteins from transcripts.<br> \
    Set verbose = true to retrieve full info on the proteins.<br> Example: region = chr16:67562500-67640000, transcript_type = protein_coding, transcript_id = ENST00000401394 (Ensembl ID)<br>The limit parameter controls the page size and can not exceed 100.',
  proteins_transcripts: 'Retrieve transcripts from proteins.<br> \
    Set verbose = true to retrieve full info on the transcripts.<br> Example: protein_name = CTCF_HUMAN, dbxrefs = ENSP00000494538.1, protein_id = P49711<br>The limit parameter controls the page size and can not exceed 100.',
  genes_genes: 'Retrieve coexpressed gene pairs from CoXPresdb and genetic interactions from BioGRID.<br> The following parameters can be used to set thresholds on z_score from CoXPresdb: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Example: gene_id = ENSG00000121410, gene_name = A1BG, z_score = gt:4. The limit parameter controls the page size and can not exceed 100.',
  variants: 'Retrieve genetic variants.<br> Example: region = chr1:1157520-1158189, funseq_description = coding (or noncoding), rsid = rs58658771, <br>variant_id = 77e1ee142a7ed70fd9dd36513ef1b943fdba46269d76495a392cf863869a8dcb (internal hashed variant ids). <br>funseq_description value is only used for human variants. mouse_strain value is only used for mouse variants. <br>The limit parameter controls the page size and can not exceed 500.',
  variants_summary: 'Retrieve genetic variants summary.<br> Example: variant_id = 902c62e8f180008b795a2c931d53b1acc4c3642009a80e0985c734a8d206c8f6 (internal hashed variant ids).',
  variants_by_freq: 'Retrieve genetic variants within a genomic region by frequencies.<br> Example: region = chr3:186741137-186742238, source = bravo_af, GENCODE_category = coding (or noncoding), minimum_af: 0.1, maximum_af:0.8',
  variants_variants: 'Retrieve genetic variants in linkage disequilibrium (LD).<br> The following parameters can be used to set thresholds on r2 and d_prime: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the variants.<br>  Example: variant_id = ec046cdcc26b8ee9e79f9db305b1e9d5a6bdaba2d2064176f9a4ea50007b1e9a, chr = chr11, position (zero base) = 9083634, spdi = NC_000011.10:9083634:A:T, hgvs = NC_000011.10:g.9083635A>T, rsid = rs60960132, r2 = gte:0.8, d_prime = gt:0.9, ancestry = EUR. The limit parameter controls the page size and can not exceed 500.',
  variants_genes: 'Retrieve variant-gene pairs from GTEx eQTLs & splice QTLs by internal variant ids.<br> The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the corresponding variants and genes.<br> Example: variant_id = 22f170e54c30a59e737beba20444f192201126f0b1415a7c9a106d1d01fe98d0, log10pvalue = gte:2',
  genes_variants: 'Retrieve variant-gene pairs from GTEx eQTLs & splice QTLs by Ensembl gene ids.<br> The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the corresponding variants and genes.<br> Example: gene_id = ENSG00000187642, log10pvalue = gte:2',
  motifs: 'Retrieve transcription factor binding motifs from HOCOMOCO.<br> Example: tf_name = STAT3_HUMAN. . The limit parameter controls the page size and can not exceed 500.',
  motifs_proteins: 'Retrieve proteins for motifs.<br> Set verbose = true to retrieve full info on the proteins.<br> Example: name = ATF1_HUMAN, source = HOCOMOCOv11.<br>The limit parameter controls the page size and can not exceed 1000.',
  proteins_motifs: 'Retrieve motifs for proteins.<br> Set verbose = true to retrieve full info on the motifs.<br> Example: protein_id = P18846 (Uniprot ID), protein_name = ATF1_HUMAN, full_name = Cyclic AMP-dependent transcription factor ATF-1, \
  dbxrefs = ENSP00000262053.3.<br>The limit parameter controls the page size and can not exceed 1000.',
  phenotypes_variants: 'Retrieve variant-trait pairs from GWAS by phenotypes.<br> The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the studies.<br> Example: term_id (phenotype ID) = EFO_0007937, term_name = blood protein measurement, log10pvalue = gte:5<br>The limit parameter controls the page size and can not exceed 100.',
  variants_phenotypes: 'Retrieve variant-trait pairs from GWAS by variants. Filters on phenotype ontology id can be used together.<br> The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the ontology terms of the traits.<br> Example: variant_id = 1f3e4afc831fff5a67f2401fb5dc7ef55b0e177f633b7fd88036962bacb925d9, region = chr1:1022580-1023580, rsid = rs2710889, phenotype_id = EFO_0004339, log10pvalue = gte:5<br>The limit parameter controls the page size and can not exceed 100.',
  diseases_genes: 'Retrieve disease-gene pairs from Orphanet by diseases.<br> \
    Set verbose = true to retrieve full info on the genes.<br> Example: disease_name = fibrosis or disease_id = Orphanet_586. Either term_name or disease_id are required.<br>The limit parameter controls the page size and can not exceed 100.',
  genes_diseases: 'Retrieve disease-gene pairs from Orphanet by genes.<br> \
    Set verbose = true to retrieve full info on the disease terms.<br> Example: gene_name = KCNN4, region = chr19:43764000-43784000, gene_type = protein_coding, alias = DHS2, gene_id = ENSG00000170558 (Ensembl ID).<br>The limit parameter controls the page size and can not exceed 100.',
  ontology_terms: 'Retrieve ontology terms.<br> Example: term_id = Orphanet_101435, name = Rare genetic eye disease, synonyms = WTC11, source = EFO, subontology= molecular_function. The limit parameter controls the page size and can not exceed 1000.',
  ontology_terms_search: 'Retrieve ontology terms by searching term names.<br> Example: term = liver',
  go_mf: 'Retrieve the GO (Gene Ontology) terms for molecular functions.<br> Example: term_id = GO_0001545, term_name = primary ovarian follicle growth, primary ovarian follicle growth, primary ovarian follicle growth',
  go_cc: 'Retrieve the GO (Gene Ontology) terms for cellular components.<br> Example: term_id = GO_0001673, term_name = male germ cell nucleus, male germ cell nucleus, male germ cell nucleus',
  go_bp: 'Retrieve the GO (Gene Ontology) terms for biological processes.<br> Example: term_id = GO_0001664, term_name = G protein-coupled receptor binding, G protein-coupled receptor binding, G protein-coupled receptor binding',
  ontology_terms_children: 'Retrieve all child nodes of an ontology term.<br> Example: ontology_term_id = UBERON_0003661. The limit parameter controls the page size and can not exceed 500.',
  ontology_terms_parents: 'Retrieve all parent nodes of an ontology term.<br> Example: ontology_term_id = UBERON_0014892. The limit parameter controls the page size and can not exceed 500.',
  ontology_terms_transitive_closure: 'Retrieve all paths between two ontology terms (i.e. transitive closure).<br> Example: ontology_term_id_start = UBERON_0003663, ontology_term_id_end = UBERON_0014892',
  variants_proteins: 'Retrieve allele-specific transcription factor binding events from ADASTRA in cell type-specific context, allele-specific transcription factor binding events from GVATdb, and pQTL from UKB by querying variants.<br> \
  Set verbose = true to retrieve full info on the variant-transcription factor pairs, and ontology terms of the cell types.<br> Example: spdi = NC_000020.11:3658947:A:G, hgvs = NC_000020.11:g.3658948A>G, <br>variant_id = 027a180998e6da9822221181225654b628ecfe93fd7a23da92d1e4b9bc8db152 (internal hashed variant ids), rsid = rs6139176.<br> The limit parameter controls the page size and can not exceed 100.',
  proteins_variants: 'Retrieve allele-specific transcription factor binding events from ADASTRA in cell type-specific context, allele-specific transcription factor binding events from GVATdb, and pQTL from UKB by querying proteins.<br> \
  Set verbose = true to retrieve full info on the ontology terms of the cell types.<br> Example: protein_id = P49711, protein_name = CTCF_HUMAN, full_name = Transcriptional repressor CTCF, dbxrefs = ENSP00000264010.<br> The limit parameter controls the page size and can not exceed 100.',
  autocomplete: 'Autocomplete names for genes, proteins and ontology terms.<br> Example: term = ZNF, type = gene',
  complex: 'Retrieve complexes.<br> Example: complex_id: CPX-11, name: SMAD2, description: phosphorylation',
  complexes_proteins: 'Retrieve protein participants for complexes.<br> \
  Set verbose = true to retrieve full info on the proteins.<br> Example: complex_id: CPX-9, complex_name: SMAD2, description: phosphorylation.<br>The limit parameter controls the page size and can not exceed 50.',
  proteins_complexes: 'Retrieve complexes by querying from protein participants.<br> \
  Set verbose = true to retrieve full info on the complexes.<br> Example: protein_id = Q15796 (uniprot ids), name = SMAD2_HUMAN, <br>full_name = Mothers against decapentaplegic homolog 2, dbxrefs = ENSP00000349282.4',
  drugs: 'Retrieve drugs (chemicals). Example: drug_id = PA448497 (chemical ids from pharmGKB), drug_name = aspirin.<br>The limit parameter controls the page size and can not exceed 1000.',
  drugs_variants: 'Retrieve variants associated with the query drugs from pharmGKB.<br> Set verbose = true to retrieve full info on the variants.<br> \
  Example: drug_id = PA448497, drug_name = aspirin, (at least one of the drug fields needs to be specified), <br> \
  the following filters on variants-drugs association can be combined for query: pmid = 20824505, phenotype_categories = Toxicity. <br> The limit parameter controls the page size and can not exceed 100.',
  variants_drugs: 'Retrieve drugs associated with the query variants from pharmGKB.<br> Set verbose = true to retrieve full info on the drugs.<br> \
  Example: spdi = NC_000001.11:230714139:T:G, hgvs = NC_000001.11:g.230714140T>G, <br>variant_id = b8d8a33facd5b62cb7f1004ae38419b8d914082ea9b217bef008a6a7f0218687, rsid = rs5050 (at least one of the variant fields needs to be specified), <br> \
  the following filters on variants-drugs association can be combined for query: pmid = 20824505, phenotype_categories = Toxicity. <br> The limit parameter controls the page size and can not exceed 100.',
  studies: 'Retrieve studies from GWAS. Example: study_id: GCST007798, pmid: 30929738',
  proteins_proteins: 'Retrieve protein-protein interactions.<br> \
  Set verbose = true to retrieve full info on the proteins. <br> Example: protein_id = P31946, name = 1433B_HUMAN, <br> \
  detection method = affinity chromatography technology, <br>interaction type = physical association, pmid = 28514442, source = BioGRID. <br> The limit parameter controls the page size and can not exceed 250.',
  mm_regulatory_regions: 'Retrieve mouse regulatory regions.<br> Example: region = chr1:2035821-3036921, biochemical_activity = CA, source = ENCODE_SCREEN (ccREs)',
  genes_proteins_variants: 'Retrieve variants associated with genes or proteins that match a query. Example: query = ATF1.<br>The limit parameter controls the page size and can not exceed 100.',
  variants_genes_proteins: 'Retrieve genes and proteins associated with a variant matched by ID. Example: variant_id = 0002fc5172fff77c908e59d5d1803d8b657e3e1c908a74849758f209738df41f.<br>The limit parameter controls the page size and can not exceed 100.',
  genes_proteins_genes_proteins: 'Retrieve genes or proteins associated with either genes or proteins that match a query. Example: query = ENSG00000123268.<br>The limit parameter controls the page size of related items and can not exceed 100.',
  regulatory_regions_biosamples: 'Retrieve MPRA experiments by querying positions of regulatory regions.<br> Set verbose = true to retrieve full info on the cell ontology terms.<br> \
  Example: type = MPRA_expression_tested, region = chr10:100038743-100038963<br>The limit parameter controls the page size and can not exceed 50.',
  biosamples_regulatory_regions: 'Retrieve MPRA expriments by querying cell ontology terms.<br> Set verbose = true to retrieve full info on the tested regulatory regions.<br> \
  Example: type = MPRA_expression_tested, biosample_id = EFO_0001187, biosample_name = hepg2, biosample_synonyms = WTC11.<br>The limit parameter controls the page size and can not exceed 50.',
  annotations_go_terms: 'Retrieve GO annotations from either proteins or transcripts. Example: query = ATF1_HUMAN or query = ENST00000663609.<br>The limit parameter controls the page size and can not exceed 100.',
  go_terms_annotations: 'Retrieve annotations associated with a GO term. Example: go_term_id: GO_1990590.<br>The limit parameter controls the page size and can not exceed 100.',
  coding_variants: 'Retrieve coding variants annotations. Example: name: SAMD11_p.Lys3Ter, hgvsp: p.Lys3Ter, gene_name: SAMD11, protein_name: SAM11_HUMAN, position: 1 (range values are also available, e.g: range:0-2), transcript_id: ENST00000342066.<br>The limit parameter controls the page size and can not exceed 25.',
  nearest_genes: 'Retrieve a list of human genes if region is in a coding variant. Otherwise, it returns the nearest human genes on each side. Example: region = chr1:11868-14409 or region = chr1:1157520-1158189'
}
