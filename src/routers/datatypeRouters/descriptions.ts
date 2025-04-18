/* eslint-disable no-multi-str */
export const descriptions = {
  genomic_elements: 'Retrieve genomic elements.<br> \
  Example: region = chr1:1157520-1158189, <br> \
  source_annotation = dELS: distal Enhancer-like signal, <br> \
  type = candidate cis regulatory element, <br> \
  source = ENCODE_SCREEN (ccREs). <br> \
  The limit parameter controls the page size and can not exceed 1000. <br> \
  Pagination is 0-based.',

  genomic_elements_genes: 'Retrieve genomic elements and gene pairs by querying genomic elements.<br> \
  Region is required. Example region = chr1:903900-904900;  source_annotation = enhancer. <br> <br> \
  You can further filter the results by biosample. For example: <br> \
  biosample_id = CL_0000127, <br> \
  biosample_name = astrocyte, <br> \
  biosample_synonyms = astrocytic glia. <br> \
  Filters on source, region_type and source_annotation work only in specific combinations based on data availability. <br> \
  For example: <br> \
  1. source = ENCODE_EpiRaction, <br> \
   region_type = accessible dna elements; <br> \
   source_annotation = enhancer. <br> \
  2. source = ENCODE-E2G-DNaseOnly and ENCODE-E2G-Full, <br> \
   region_type = accessible dna elements; <br> \
   source_annotation = enhancer. <br> \
  3. source = ENCODE-E2G-CRISPR, region_type = tested elements <br> \
  [Note: the enhancers list includes all elements that were found to be positive (with significant = True) <br> \
  for any tested gene while the tested elements lists all the elements ever tested but found to be negative (with significant = False) for all tested genes] ; <br> \
  source_annotation = enhancer (positive cases) or negative control (negative cases). <br>\
  Set verbose = true to retrieve full info on the genes, genomic element and biosamples.<br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  genes_genomic_elements: 'Retrieve genomic elements - gene pairs by querying genes.<br> \
  Set verbose = true to retrieve full info on the genes, genomic elements and biosamples.<br> \
  Example: gene_id = ENSG00000187634, gene_name = SAMD11, <br> \
  alias = CKLF, <br> \
  hgnc = HGNC:28208. <br> \
  You can further filter the results by biosample. For example: <br> \
  biosample_id = CL_0000127, <br> \
  biosample_name = astrocyte, <br> \
  biosample_synonyms = astrocytic glia. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  genes: 'Retrieve genes.<br> \
  Example: organism = Homo sapiens, <br> \
  name = SAMD1, <br> \
  region = chr1:212565300-212620800, <br> \
  alias = CKLF, <br> \
  gene_id = ENSG00000187642 (Ensembl ids), <br> \
  gene_type = protein_coding, <br> \
  hgnc = HGNC:28208. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  genes_structure: 'Retrieve genes structure.<br> \
  you can filter by one of the four categories: gene, transcript, protein or region. <br> \
  Example: organism = Homo sapiens, <br> \
  region = chr1:212565300-212620800, <br> \
  gene_id = ENSG00000187642 (Ensembl ids), <br> \
  gene_name = ATF3, <br> \
  transcript_id = ENST00000443707 (Ensembl ids), <br> \
  transcript_id = TNF-207, <br> \
  protein_id = P49711, <br> \
  protein_name = SMAD1_HUMAN. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  transcripts: 'Retrieve transcripts. <br> \
  Example: region = chr20:9537369-9839076, <br> \
  transcript_type = protein_coding, <br> \
  transcript_id = ENST00000443707 (Ensembl ids). <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  proteins: 'Retrieve proteins.<br> \
  Example: name = 1433B_HUMAN, <br> \
  dbxrefs = ENSP00000494538.1, <br> \
  protein_id = P49711 (Uniprot ids). <br> \
  The limit parameter controls the page size and can not exceed 50. <br> \
  Pagination is 0-based.',

  genes_transcripts: 'Retrieve transcripts from genes.<br> \
    Set verbose = true to retrieve full info on the transcripts.<br> \
    Example: gene_name = ATF3, hgnc = HGNC:28208, <br> \
    alias = CKLF, gene_id = ENSG00000187642 (Ensembl ids). <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based.',

  transcripts_genes: 'Retrieve genes from transcripts.<br> \
    Set verbose = true to retrieve full info on the genes.<br> \
    Example: region = chr1:711800-740000, <br> \
    transcript_id = ENST00000443707 (Ensembl ID). <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based.',

  genes_proteins: 'Retrieve proteins from genes.<br> \
  Set verbose = true to retrieve full info on the proteins. <br> \
  Example: gene_name = ATF3, <br> \
  alias = CKLF, <br> \
  gene_id = ENSG00000170558 (Ensembl ID), <br> \
  hgnc = HGNC:13723. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  proteins_genes: 'Retrieve genes from proteins.<br> \
  Set verbose = true to retrieve full info on the genes.<br> \
  Example: protein_name = SMAD1_HUMAN, <br> \
  protein_id = Q15797, <br> \
  full_name = Mothers against decapentaplegic homolog 1, <br> \
  dbxrefs = HGNC:6767. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  transcripts_proteins: 'Retrieve proteins from transcripts.<br> \
    Set verbose = true to retrieve full info on the proteins.<br> \
    Example: region = chr16:67562500-67640000, <br> \
    transcript_type = protein_coding, <br> \
    transcript_id = ENST00000401394 (Ensembl ID). <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based.',

  variants_variants_summary: 'Retrieve a summary of genetic variants in linkage disequilibrium (LD).<br> \
    Example: variant_id = ec046cdcc26b8ee9e79f9db305b1e9d5a6bdaba2d2064176f9a4ea50007b1e9a, hgvs = NC_000011.10:g.9090011A>G, spdi = NC_000011.10:9090010:A:G. The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based.',

  variants_genes_summary: 'Retrieve a summary of associated genes from GTEx eQTLs & splice QTLs by internal variant ids.<br> \
    Example: variant_id = c41b54297becfa593170b5a7e29199d17e06cda37bff9edea5e5b8b333f95a70, spdi = NC_000001.11:920568:G:A, hgvs = NC_000001.11:g.920569G>A. <br> \
    Pagination is 0-based.',

  proteins_transcripts: 'Retrieve transcripts from proteins.<br> \
    Set verbose = true to retrieve full info on the transcripts.<br> \
    Example: protein_name = CTCF_HUMAN, <br> \
    dbxrefs = ENSP00000494538.1, <br> \
    protein_id = P49711. <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based.',

  genes_genes: 'Retrieve coexpressed gene pairs from CoXPresdb and genetic interactions from BioGRID. <br> \
  The following parameters can be used to set thresholds on z_score from CoXPresdb: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Example: organism = Homo sapiens or Mus musculus, <br> \
    source = CoXPresdb, <br> \
    interaction_type = dosage growth defect (sensu BioGRID), <br> \
    gene_id = ENSG00000121410, <br> \
    hgnc = HGNC:5, <br> \
    gene_name = A1BG, <br> \
    alias = HYST2477, <br> \
    z_score = gt:4. <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based.',

  variants: 'Retrieve genetic variants.<br> \
  Example: organism = Homo sapiens or Mus musculus.<br> \
  mouse_strain = CAST_EiJ (only for mouse variants). <br> \
  The examples below are specific to Homo sapiens: <br> \
  region = chr1:1157520-1158189, <br> \
  GENCODE_category = coding or noncoding (only for human variants), <br> \
  rsid = rs58658771,  <br> \
  spdi = NC_000020.11:3658947:A:G, <br> \
  hgvs = NC_000020.11:g.3658948A>G, <br> \
  variant_id = 77e1ee142a7ed70fd9dd36513ef1b943fdba46269d76495a392cf863869a8dcb (internal hashed variant ids). <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  variants_summary: 'Retrieve genetic variants summary.<br> \
   Example: variant_id = 902c62e8f180008b795a2c931d53b1acc4c3642009a80e0985c734a8d206c8f6 (internal hashed variant ids). <br> \
   Pagination is 0-based.',

  variants_alleles: 'Retrieve GNOMAD alleles for variants in a given region.<br> \
   Example: region = chr1:1157520-1158520.<br> \
   Region limit: 1kb pairs. <br> \
   Pagination is 0-based.',

  variants_by_freq: 'Retrieve genetic variants within a genomic region by frequencies.<br> \
   Example: region = chr3:186741137-186742238, <br> \
   source = bravo_af, <br> \
   GENCODE_category = coding (or noncoding), <br> \
   spdi = NC_000020.11:3658947:A:G, <br> \
   hgvs = NC_000020.11:g.3658948A>G, <br> \
   rsid = rs58658771, <br> \
   minimum_af: 0.1, <br> \
   maximum_af:0.8. <br> \
   Pagination is 0-based.',

  variants_variants: 'Retrieve genetic variants in linkage disequilibrium (LD).<br> \
   The following parameters can be used to set thresholds on r2 and d_prime: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the variants.<br>  \
    Example: variant_id = ec046cdcc26b8ee9e79f9db305b1e9d5a6bdaba2d2064176f9a4ea50007b1e9a,<br> \
    chr = chr11, position (zero base) = 9083634, <br> \
    spdi = NC_000011.10:9083634:A:T, <br> \
    hgvs = NC_000011.10:g.9083635A>T, <br> \
    rsid = rs60960132, <br> \
    r2 = gte:0.8, <br> \
    d_prime = gt:0.9, <br> \
    ancestry = EUR. <br> \
    The limit parameter controls the page size and can not exceed 500. <br> \
    Pagination is 0-based.',

  variants_genes: 'Retrieve variant-gene pairs from GTEx eQTLs & splice QTLs by internal variant ids.<br> \
  The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the corresponding variants and genes.<br> \
    Example: variant_id = 22f170e54c30a59e737beba20444f192201126f0b1415a7c9a106d1d01fe98d0, <br> \
    log10pvalue = gte:2, <br> \
    effect_size = lte:0.001, <br> \
    label = eQTL (should pass other parameters such as source along with label), <br> \
    source = GTEx. <br> \
    The limit parameter controls the page size and can not exceed 500. <br> \
    Pagination is 0-based.',

  genes_variants: 'Retrieve variant-gene pairs from GTEx eQTLs & splice QTLs by Ensembl gene ids.<br> \
  The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the corresponding variants and genes.<br> \
    Example: source = GTEx, <br> \
    gene_id = ENSG00000187642, <br> \
    hgnc = HGNC:28208, <br> \
    gene_name = SAMD11, <br> \
    alias = CKLF, <br> \
    label = eQTL, <br> \
    effect_size = lte:0.001, <br> \
    log10pvalue = gte:2. <br> \
    The limit parameter controls the page size and can not exceed 500. <br> \
    Pagination is 0-based.',

  coding_variants_variants: 'Retrieve variants associated with a coding variant.<br> \
    Example: coding_variant_name = OR4F5_ENST00000641515_p.Gly30Ser_c.88G-A, <br> \
    hgvsp = p.Gly30Ser, <br> \
    The limit parameter controls the page size and can not exceed 500. <br> \
    Pagination is 0-based.',

  variants_coding_variants: 'Retrieve coding variants from dbSNFP associated with a variant.<br> \
    Example: variant_id = 86ca552850ae74ab0e6c509a7b2c94595ad9b56fcb8388b0d5a1723970f4400c, <br> \
    spdi = NC_000001.11:942606:G:T, <br> \
    hgvs = NC_000001.11:g.942607G>T, <br> \
    The limit parameter controls the page size and can not exceed 500. <br> \
    Pagination is 0-based.',

  motifs: 'Retrieve transcription factor binding motifs from HOCOMOCO.<br> \
  Example: tf_name = STAT3_HUMAN, <br> \
  source = HOCOMOCOv11. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  motifs_proteins: 'Retrieve proteins and complexes for motifs.<br> \
  Set verbose = true to retrieve full info on the proteins and complexes.<br> \
  Example: tf_name = ATF1_HUMAN, <br> \
  source = HOCOMOCOv11. <br> \
  The limit parameter controls the page size and can not exceed 1000. <br> \
  Pagination is 0-based.',

  proteins_motifs: 'Retrieve motifs for proteins.<br> \
  Set verbose = true to retrieve full info on the motifs.<br> \
  Example: protein_id = P18846 (Uniprot ID), <br> \
  protein_name = ATF1_HUMAN, <br> \
  full_name = Cyclic AMP-dependent transcription factor ATF-1, \
  dbxrefs = ENSP00000262053.3.<br> \
  The limit parameter controls the page size and can not exceed 1000. <br> \
  Pagination is 0-based.',

  phenotypes_variants: 'Retrieve variant-trait pairs from GWAS by phenotypes.<br> \
  The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
  Set verbose = true to retrieve full info on the studies.<br> \
  Example: phenotype ID = EFO_0007937, <br> \
  phenotype_name = blood protein measurement, <br> \
  log10pvalue = gte:5. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  variants_phenotypes: 'Retrieve variant-trait pairs from GWAS by variants. <br> \
  Filters on phenotype ontology id can be used together.<br> \
  The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
  Set verbose = true to retrieve full info on the studies.<br> \
  Example: variant_id = 1f3e4afc831fff5a67f2401fb5dc7ef55b0e177f633b7fd88036962bacb925d9, <br> \
  rsid = rs2710889, <br> \
  region = chr1:1022580-1023580, <br> \
  spdi: NC_000001.11:1023572:A:G, <br> \
  hgvs: NC_000001.11:g.1009731C>T, <br> \
  chr = chr1, <br> \
  position = 1023572, <br> \
  phenotype_id = EFO_0004339, <br> \
  log10pvalue = gte:5, <br>\
  mouse_strain = CAST_EiJ, <br> \
  organism = Homo sapiens (or Mus musculus). <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  diseases_genes: 'Retrieve disease-gene pairs from Orphanet by diseases.<br> \
    Set verbose = true to retrieve full info on the genes and diseases. <br> \
    Example: disease_name = fibrosis, <br> \
    disease_id = Orphanet_586, <br> \
    Orphanet_association_type = Disease-causing genrmline mutation(s) in, <br> \
    source = Orphanet. <br> \
    Either disease_name or disease_id are required. <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based.',

  genes_diseases: 'Retrieve disease-gene pairs from Orphanet and ClinGen by genes.<br> \
    Set verbose = true to retrieve full info on the disease terms, and the variants associated with the disease from ClinGen. <br> \
    Example: gene_id = ENSG00000171759, <br> \
    gene_name = PAH, <br> \
    alias = PKU1, <br> \
    hgnc = HGNC:8582. <br> \
    The limit parameter controls the page size and can not exceed 25. <br> \
    Pagination is 0-based.',

  ontology_terms: 'Retrieve ontology terms.<br> \
  Example: term_id = Orphanet_101435, <br> \
  name = Rare genetic eye disease, <br> \
  synonyms = WTC11, <br> \
  source = EFO, <br> \
  subontology= molecular_function. <br> \
  The limit parameter controls the page size and can not exceed 1000. <br> \
  Pagination is 0-based.',

  ontology_terms_children: 'Retrieve all child nodes of an ontology term.<br> \
  Example: ontology_term_id = CHEBI_20857. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  ontology_terms_parents: 'Retrieve all parent nodes of an ontology term.<br> \
  Example: ontology_term_id = CHEBI_100001. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  ontology_terms_transitive_closure: 'Retrieve all paths between two ontology terms (i.e. transitive closure).<br> \
  Example: ontology_term_id_start = UBERON_0003663, <br> \
  ontology_term_id_end = UBERON_0014892',

  variants_proteins: 'Retrieve allele-specific transcription factor binding events from ADASTRA in cell type-specific context, <br> \
   allele-specific transcription factor binding events from GVATdb, pQTL from UKB by querying variants, and predicted allele specific binding from SEMpl.<br> \
  Set verbose = true to retrieve full info on the variant-transcription factor pairs, and ontology terms of the cell types.<br> \
  Example: variant_id = 027a180998e6da9822221181225654b628ecfe93fd7a23da92d1e4b9bc8db152 (internal hashed variant ids), <br> \
  spdi = NC_000020.11:3658947:A:G, <br> \
  hgvs = NC_000020.11:g.3658948A>G, <br> \
  rsid = rs6139176,<br> \
  chr = chr20, <br> \
  position = 3658947, <br> \
  organism = Homo sapiens, <br> \
  label = pQTL (or allele-specific binding), <br> \
  source = UKB. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  proteins_variants: 'Retrieve allele-specific transcription factor binding events from ADASTRA in cell type-specific context, <br> \
   allele-specific transcription factor binding events from GVATdb, pQTL from UKB by querying proteins, and predicted allele specific binding from SEMpl.<br> \
  Set verbose = true to retrieve full info on the variant-transcription factor pairs, and the ontology terms of the cell types.<br> \
  Example: protein_id = P49711, <br> \
  protein_name = CTCF_HUMAN, <br> \
  full_name = Transcriptional repressor CTCF, <br> \
  dbxrefs = ENSG00000102974.<br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  autocomplete: 'Autocomplete names for genes, proteins and ontology terms.<br> \
  Example: term = ZNF, <br> \
  type = gene <br> \
  Pagination is 0-based.',

  complex: 'Retrieve complexes.<br> \
  Example: complex_id = CPX-11, <br> \
  name = SMAD2, <br> \
  description = phosphorylation. <br> \
  Pagination is 0-based.',

  complexes_proteins: 'Retrieve protein participants for complexes.<br> \
  Set verbose = true to retrieve full info on the proteins.<br> \
  Example: complex_id = CPX-9, <br> \
  complex_name = SMAD2, <br> \
  description = phosphorylation.<br> \
  The limit parameter controls the page size and can not exceed 50. <br> \
  Pagination is 0-based.',

  proteins_complexes: 'Retrieve complexes by querying from protein participants.<br> \
  Set verbose = true to retrieve full info on the complexes.<br> \
  Example: protein_id = Q15796 (uniprot ids), <br> \
  protein_name = SMAD2_HUMAN, <br> \
  full_name = Mothers against decapentaplegic homolog 2, <br> \
  dbxrefs = ENSP00000349282.4. <br> \
  Pagination is 0-based.',

  drugs: 'Retrieve drugs (chemicals). <br> \
  Example: drug_id = PA448497 (chemical ids from pharmGKB), <br> \
  name = aspirin.<br> \
  The limit parameter controls the page size and can not exceed 1000. <br> \
  Pagination is 0-based.',

  drugs_variants: 'Retrieve variants associated with the query drugs from pharmGKB.<br> \
  Set verbose = true to retrieve full info on the variants. <br> \
  Example: drug_id = PA448497, <br> \
  drug_name = aspirin, (at least one of the drug fields needs to be specified), <br> \
  the following filters on variants-drugs association can be combined for query: <br> \
  pmid = 20824505, <br> \
  phenotype_categories = Toxicity. <br> \
  organism = Homo sapiens. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  variants_drugs: 'Retrieve drugs associated with the query variants from pharmGKB.<br> \
  Set verbose = true to retrieve full info on the drugs.<br> \
  Example: variant_id = b8d8a33facd5b62cb7f1004ae38419b8d914082ea9b217bef008a6a7f0218687, <br> \
  spdi = NC_000001.11:230714139:T:G, <br> \
  hgvs = NC_000001.11:g.230714140T>G, <br> \
  rsid = rs5050 (at least one of the variant fields needs to be specified), <br> \
  the following filters on variants-drugs association can be combined for query: <br> \
  GENCODE_category = coding (or noncoding), <br> \
  pmid = 20824505, <br> \
  phenotype_categories = Toxicity. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  studies: 'Retrieve studies from GWAS. <br> \
  Example: study_id = GCST007798, <br> \
  pmid = 30929738. <br> \
  Pagination is 0-based.',

  genes_predictions: 'Retrieve element gene predictions associated with a given gene.<br> \
  Example: gene_id = ENSG00000187961.<br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  variants_genomic_elements: 'Retrieve element gene predictions associated with a given variant.<br> \
  Example: variant_id = 002f7f9491550fa5e17fbfa2322a27a0f117b45fc8ff306863a689b26f1e2d23, hgvs = NC_000001.11:g.1629000del,<br> \
  spdi = NC_000001.11:1628997:GGG:GG, rsid = rs1317845941.<br> \
  The limit parameter controls the page size and can not exceed 300. <br> \
  Pagination is 0-based.',

  variants_genomic_elements_count: 'Retrieve counts of element gene predictions and cell types associated with a given variant.<br> \
  Example: variant_id = 002f7f9491550fa5e17fbfa2322a27a0f117b45fc8ff306863a689b26f1e2d23, hgvs = NC_000001.11:g.1629000del,<br> \
  spdi = NC_000001.11:1628997:GGG:GG, rsid = rs1317845941',

  proteins_proteins: 'Retrieve protein-protein interactions.<br> \
  Set verbose = true to retrieve full info on the proteins. <br> \
  Example: protein_id = P31946, <br> \
  protein_name = 1433B_HUMAN, <br> \
  full_name = Pantothenate kinase 3, <br> \
  dbxrefs = ENSP00000494538.1. <br> \
  detection method = affinity chromatography technology, <br> \
  interaction type = physical association, <br> \
  pmid = 28514442, <br> \
  source = BioGRID. <br> \
  The limit parameter controls the page size and can not exceed 250. <br> \
  Pagination is 0-based.',

  genes_proteins_variants: 'Retrieve variants associated with genes or proteins that match a query. <br> \
  Example: query = ATF1.<br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  variants_genes_proteins: 'Retrieve genes and proteins associated with a variant matched by ID. <br> \
  Example: variant_id = 0002fc5172fff77c908e59d5d1803d8b657e3e1c908a74849758f209738df41f.<br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  genes_proteins_genes_proteins: 'Retrieve genes or proteins associated with either genes or proteins that match a query. <br> \
  Example: query = ENSG00000123268.<br> \
  The limit parameter controls the page size of related items and can not exceed 100. <br> \
  Pagination is 0-based.',

  genomic_elements_biosamples: 'Retrieve MPRA experiments by querying positions of genomic elements. <br> \
  Set verbose = true to retrieve full info on the cell ontology terms. <br> \
  Example: region_type = tested elements, region = chr10:100038743-100038963. <br> \
  The limit parameter controls the page size and can not exceed 50. <br> \
  Pagination is 0-based.',

  biosamples_genomic_elements: 'Retrieve MPRA expriments by querying cell ontology terms. <br> \
  Set verbose = true to retrieve full info on the tested genomic elements. <br> \
  Example: biosample_id = EFO_0001187, <br> \
  biosample_name = hepg2, <br> \
  biosample_synonyms = WTC11. <br> \
  The limit parameter controls the page size and can not exceed 50. <br> \
  Pagination is 0-based.',

  annotations_go_terms: 'Retrieve GO annotations from either proteins or transcripts. <br> \
  Example: query = ATF1_HUMAN or query = ENST00000663609. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  go_terms_annotations: 'Retrieve annotations associated with a GO term. <br> \
  Example: go_term_id = GO_1990590. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  coding_variants: 'Retrieve coding variants annotations. <br> \
  Example: name = SAMD11_ENST00000420190_p.Ala3Gly_c.8C>G, <br> \
  id = SAMD11_ENST00000420190_p.Ala3Gly_c.8C-G, <br> \
  hgvsp = p.Lys3Ter, <br> \
  gene_name = SAMD11, <br> \
  protein_id = Q494U1, <br> \
  protein_name = SAM11_HUMAN, <br> \
  amino_acid_position = 1 (range values are also available, e.g: range:0-2), <br> \
  transcript_id = ENST00000342066.<br> \
  The limit parameter controls the page size and can not exceed 25. <br> \
  Pagination is 0-based.',

  nearest_genes: 'Retrieve a list of human genes if region is in a coding variant. Otherwise, it returns the nearest human genes on each side. <br> \
  Example: region = chr1:11868-14409 or region = chr1:1157520-1158189.',

  variants_diseases: 'Retrieve diseases and genes associated with the query variant from ClinGen. <br> \
  Example: variant_id = e4b5a3b5c96984f03ed0a79dca6342d3d74cbc642ae1ea589f409c04ccc3044f <br> \
  spdi = NC_000012.12:102917129:T:C, <br> \
  hgvs = NC_000012.12:g.102917130T>C, <br> \
  rsid = rs62514891, <br> \
  chr = chr12, <br> \
  position (zero base) = 102917129, <br> \
  pmid = 2574002. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  diseases_variants: 'Retrieve variants and genes associated with the query disease from ClinGen. <br> \
  Example: disease_id = MONDO_0009861, <br> \
  disease_name = phenylketonuria, <br> \
  pmid = 2574002. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  pathways: 'Retrieve pathways from Reactome.<br> \
  Example: id = R-HSA-164843, <br> \
  name = 2-LTR circle formation, <br> \
  is_in_disease = true. <br> \
  name_aliases = 2-LTR circle formation, <br> \
  is_top_level_pathway = true. <br> \
  disease_ontology_terms = DOID_526, <br> \
  go_biological_process = GO_0006015. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  genes_pathways: 'Retrieve pathways from genes.<br> \
  Set verbose = true to retrieve full info on the pathways and genes. <br> \
  Example: gene_id = ENSG00000000419, <br> \
  hgnc = HGNC:28208, <br> \
  gene_name = PERM1, <br> \
  alias = CKLF. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  pathways_genes: 'Retrieve genes from pathways.<br> \
  Set verbose = true to retrieve full info on the genes. <br> \
  Example: id = R-HSA-164843, <br> \
  name = 2-LTR circle formation, <br> \
  name_aliases = 2-LTR circle formation, <br> \
  disease_ontology_terms = DOID_526, <br> \
  go_biological_process = GO_0006015. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  pathways_pathways: 'Retrieve related pathway pairs from Reactome. <br> \
  Set verbose = true to retrieve full info on the pathway pairs. <br> \
  Example: id = R-HSA-164843, <br> \
  name = 2-LTR circle formation, <br> \
  name_aliases = 2-LTR circle formation, <br> \
  disease_ontology_terms = DOID_526, <br> \
  go_biological_process = GO_0006015. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  phenotypes_coding_variants: 'Retrieve coding variants associated with the query phenotype.<br> \
  Set verbose = true to retrieve full info for the pairs.<br> \
  Example: phenotype ID = OBA_0000128, <br> \
  phenotype_name = protein stability, <br> \
  source = VAMP-seq. <br> \
  organism = Homo sapiens. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  coding_variants_phenotypes: 'Retrieve phenotypes associated with the query coding variant. <br> \
  Set verbose = true to retrieve full info for the pairs.<br> \
  Example: coding_variant_name = CYP2C19_ENST00000371321_p.Ala103Cys_c.307_309delinsTGT, <br> \
  hgvsp = p.Ala103Cys, <br> \
  protein_name = CP2CJ_HUMAN, <br> \
  gene_name: CYP2C19, <br> \
  amino_acid_position: 103, <br> \
  transcript_id = ENST00000371321, <br> \
  source = VAMP-seq. <br> \
  organism = Homo sapiens. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.'
}
