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

  genes: 'Retrieve genes.<br> \
  Example: organism = Homo sapiens, <br> \
  name = SAMD1, <br> \
  region = chr1:212565300-212620800, <br> \
  synonym = CKLF, <br> \
  collection = ACMG73, <br> \
  study_set = MorPhiC, <br> \
  gene_id = ENSG00000187642 (Ensembl ids), <br> \
  gene_type = protein_coding, <br> \
  hgnc_id = HGNC:28208, <br> \
  entrez = ENTREZ:84808. <br> \
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
  protein_id = ENSP00000305769, <br> \
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
  Example: name = CTCF_HUMAN, <br> \
  full_name = Transcriptional repressor CTCF, <br> \
  dbxrefs = P49711, <br> \
  protein_id = ENSP00000384707.1 or ENSP00000384707 (Ensembl IDs) or P49711-2 (Uniprot ids). <br> \
  The limit parameter controls the page size and can not exceed 50. <br> \
  Pagination is 0-based.',

  genes_transcripts: 'Retrieve transcripts from genes.<br> \
    Set verbose = true to retrieve full info on the transcripts.<br> \
    Example: gene_name = ATF3, hgnc_id = HGNC:28208, <br> \
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
  hgnc_id = HGNC:13723. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  proteins_genes: 'Retrieve genes from proteins.<br> \
  Set verbose = true to retrieve full info on the genes.<br> \
  Example: protein_name = CTCF_HUMAN, <br> \
  protein_id = ENSP00000384707.1 or ENSP00000384707 (Ensembl IDs) or P49711-2 (Uniprot ids), <br> \
  full_name = Transcriptional repressor CTCF, <br> \
  dbxrefs = P49711. <br> \
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
    Example: variant_id = NC_000001.11:954257:G:C, hgvs = NC_000011.10:g.9090011A>G, spdi = NC_000011.10:9090010:A:G. The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based.',

  variants_genes_summary: 'Retrieve a summary of associated genes from GTEx eQTLs & splice QTLs by internal variant ids.<br> \
    Example: variant_id = NC_000001.11:920568:G:A, spdi = NC_000001.11:920568:G:A, hgvs = NC_000001.11:g.920569G>A.',

  proteins_transcripts: 'Retrieve transcripts from proteins.<br> \
    Set verbose = true to retrieve full info on the transcripts.<br> \
    Example: protein_name = CTCF_HUMAN, <br> \
    full_name = Transcriptional repressor CTCF, <br> \
    dbxrefs = P49711, <br> \
    protein_id = ENSP00000384707.1 or ENSP00000384707 (Ensembl IDs) or P49711-2 (Uniprot ids). <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based.',

  genes_genes: 'Retrieve coexpressed gene pairs from CoXPresdb and genetic interactions from BioGRID. <br> \
  The following parameters can be used to set thresholds on z_score from CoXPresdb: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Example: organism = Homo sapiens or Mus musculus, <br> \
    source = CoXPresdb, <br> \
    interaction_type = dosage growth defect (sensu BioGRID), <br> \
    gene_id = ENSG00000121410, <br> \
    hgnc_id = HGNC:5, <br> \
    gene_name = A1BG, <br> \
    alias = HYST2477, <br> \
    z_score = gt:4. <br> \
    name = \'interacts with\' or \'coexpressed with\' <br> \
    inverse_name = \'interacts with\' or \'coexpressed with\' <br> \
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
  variant_id = NC_000020.11:3658947:A:G. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  variants_summary: 'Retrieve genetic variants summary.<br> \
   Example: variant_id = NC_000020.11:3658947:A:G, <br> \
   spdi = NC_000020.11:3658947:A:G, <br> \
   hgvs = NC_000020.11:g.3658948A>G.',

  variants_alleles: 'Retrieve GNOMAD alleles for variants in a given region.<br> \
   Example: region = chr1:1157520-1158520.<br> \
   Region limit: 1kb pairs.',

  variants_by_freq: 'Retrieve genetic variants within a genomic region by frequencies.<br> \
   Example: region = chr3:186741137-186742238, <br> \
   source = bravo_af, <br> \
   GENCODE_category = coding (or noncoding), <br> \
   spdi = NC_000003.12:186741142:G:A, <br> \
   hgvs = NC_000003.12:g.186741143G>A, <br> \
   rsid = rs1720801112, <br> \
   minimum_af: 0, <br> \
   maximum_af:0.8. <br> \
   Pagination is 0-based.',

  variants_variants: 'Retrieve genetic variants in linkage disequilibrium (LD).<br> \
   The following parameters can be used to set thresholds on r2 and d_prime: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the variants.<br>  \
    Example: variant_id = NC_000011.10:9083634:A:T,<br> \
    chr = chr11, position (zero base) = 9083634, <br> \
    spdi = NC_000011.10:9083634:A:T, <br> \
    hgvs = NC_000011.10:g.9083635A>T, <br> \
    rsid = rs60960132, <br> \
    r2 = gte:0.8, <br> \
    d_prime = gt:0.9, <br> \
    ancestry = EUR. <br> \
    The limit parameter controls the page size and can not exceed 500. <br> \
    Pagination is 0-based.',

  variants_genes: 'Retrieve variant-gene pairs including eQTLs & splice QTLs from AFGR, eQTL Catalogue, and IGFV by internal variant ids.<br> \
  The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the corresponding variants and genes.<br> \
    Example: spdi = NC_000001.11:630556:T:C, <br> \
    hgvs = NC_000001.11:g.630557T>C, <br> \
    variant_id = NC_000001.11:630556:T:C, <br> \
    log10pvalue = gte:2, <br> \
    effect_size = lte:0.001, <br> \
    name = \'modulates expression of\' or \'modulates splicing of\' <br> \
    inverse_name = \'expression modulated by\' or \'splicing modulated by\' <br> \
    label = eQTL (should pass other parameters such as source along with label), <br> \
    source = AFGR. <br> \
    The limit parameter controls the page size and can not exceed 500. <br> \
    Pagination is 0-based.',

  genes_variants: 'Retrieve variant-gene pairs including eQTLs & splice QTLs from AFGR, eQTL Catalogue, and IGFV by Ensembl gene ids.<br> \
  The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the corresponding variants and genes.<br> \
    Example: source = AFGR, <br> \
    gene_id = ENSG00000187642, <br> \
    hgnc_id = HGNC:28208, <br> \
    gene_name = SAMD11, <br> \
    alias = CKLF, <br> \
    label = eQTL, <br> \
    effect_size = lte:0.001, <br> \
    log10pvalue = gte:2 <br> \
    name = \'modulates expression of\' or \'modulates splicing of\' <br> \
    inverse_name = \'expression modulated by\' or \'splicing modulated by\'. <br> \
    The limit parameter controls the page size and can not exceed 500. <br> \
    Pagination is 0-based.',

  coding_variants_variants: 'Retrieve variants associated with a coding variant.<br> \
    Example: coding_variant_name = OR4F5_ENST00000641515_p.Gly30Ser_c.88G-A, <br> \
    hgvsp = p.Gly30Ser, <br> \
    The limit parameter controls the page size and can not exceed 500. <br> \
    Pagination is 0-based.',

  variants_coding_variants: 'Retrieve coding variants from dbSNFP associated with a variant.<br> \
    Example: variant_id = NC_000001.11:65564:A:T, <br> \
    spdi = NC_000001.11:65564:A:T, <br> \
    hgvs = NC_000001.11:g.65565A>T, <br> \
    The limit parameter controls the page size and can not exceed 500.',

  coding_variants_phenotypes_count: 'Retrieve counts of coding variants associated with phenotypes.<br> \
    Example: gene_id = ENSG00000165841.',

  variants_phenotypes_summary: 'Retrieve scores of variants associated with phenotypes. Via coding variants edges.<br> \
    Example: variant_id = NC_000018.10:31546002:CA:GT.',

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
  Example: protein_id = ENSP00000384707.1 or ENSP00000384707 (Ensembl IDs) or P49711-2 (Uniprot ids), <br> \
  protein_name = CTCF_HUMAN, <br> \
  full_name = Transcriptional repressor CTCF, \
  dbxrefs = P49711,<br> \
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
  Example: variant_id = NC_000001.11:1023572:A:G, <br> \
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
    hgnc_id = HGNC:8582. <br> \
    The limit parameter controls the page size and can not exceed 25. <br> \
    Pagination is 0-based.',

  ontology_terms: 'Retrieve ontology terms.<br> \
  Example: term_id = Orphanet_101435, <br> \
  name = Rare genetic eye disease, <br> \
  synonyms = WTC11, <br> \
  source = EFO, <br> \
  subontology = molecular_function. <br> \
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
  Example: variant_id = NC_000017.11:7166092:G:A, <br> \
  spdi = NC_000017.11:7166092:G:A, <br> \
  hgvs = NC_000017.11:g.7166093G>A, <br> \
  rsid = rs186021206,<br> \
  chr = chr17, <br> \
  position = 7166092, <br> \
  organism = Homo sapiens, <br> \
  label = pQTL (or allele-specific binding), <br> \
  name = \'modulates binding of\' or \'associated with levels of\',<br> \
  inverse_name = \'binding modulated by\' or \'level associated with\',<br> \
  source = UKB. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  proteins_variants: 'Retrieve allele-specific transcription factor binding events from ADASTRA in cell type-specific context, <br> \
   allele-specific transcription factor binding events from GVATdb, pQTL from UKB by querying proteins, and predicted allele specific binding from SEMpl.<br> \
  Set verbose = true to retrieve full info on the variant-transcription factor pairs, and the ontology terms of the cell types.<br> \
  Example: protein_id = ENSP00000384707.1 or ENSP00000384707 (Ensembl IDs) or P49711-2 (Uniprot ids), <br> \
  protein_name = CTCF_HUMAN, <br> \
  full_name = Transcriptional repressor CTCF, <br> \
  dbxrefs = P49711,<br> \
  name = \'modulates binding of\' or \'associated with levels of\',<br> \
  inverse_name = \'binding modulated by\' or \'level associated with\',<br> \
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
  Example: protein_id = ENSP00000411322.1 or ENSP00000411322 (Ensembl IDs) or P67870 (Uniprot ids), <br> \
  protein_name = CSK2B_HUMAN, <br> \
  full_name = Casein kinase II subunit beta, <br> \
  dbxrefs = P67870. <br> \
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
  Example: variant_id = NC_000001.11:230714139:T:G, <br> \
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
  Example: variant_id = NC_000001.11:1628997:GGG:GG, hgvs = NC_000001.11:g.1629000del,<br> \
  spdi = NC_000001.11:1628997:GGG:GG, rsid = rs1317845941.<br> \
  The limit parameter controls the page size and can not exceed 300. <br> \
  Pagination is 0-based.',

  variants_genomic_elements_edge: 'Retrieve genomic elements associated with a given variant.<br> \
  Example: variant_id = NC_000005.10:1779621:C:G, spdi = NC_000005.10:1779621:C:G,<br> \
  hgvs = NC_000005.10:g.1779622C>G, rsid = rs1735214522, region = chr5:1779619-1779629.<br> \
  The limit parameter controls the page size and can not exceed 300. <br> \
  Pagination is 0-based.',

  genomic_elements_variants_edge: 'Retrieve variants associated with genomic elements.<br> \
  Example: region = chr5:1779339-1779683, <br> \
  type = candidate cis regulatory element, <br> \
  The limit parameter controls the page size and can not exceed 300. <br> \
  Pagination is 0-based.',

  variants_genomic_elements_count: 'Retrieve counts of element gene predictions and cell types associated with a given variant.<br> \
  Example: variant_id = NC_000001.11:1628997:GGG:GG, hgvs = NC_000001.11:g.1629000del,<br> \
  spdi = NC_000001.11:1628997:GGG:GG, rsid = rs1317845941',

  proteins_proteins: 'Retrieve protein-protein interactions.<br> \
  Set verbose = true to retrieve full info on the proteins. <br> \
  Example: protein_id = ENSP00000384707.1 or ENSP00000384707 (Ensembl IDs) or P49711-2 (Uniprot ids), <br> \
  protein_name = CTCF_HUMAN, <br> \
  full_name = Transcriptional repressor CTCF, <br> \
  dbxrefs = P49711, <br> \
  detection_method = affinity chromatography technology, <br> \
  interaction_type = physical association, <br> \
  pmid = 28514442, <br> \
  source = BioGRID. <br> \
  The limit parameter controls the page size and can not exceed 250. <br> \
  Pagination is 0-based.',

  genes_proteins_variants: 'Retrieve variants associated with genes or proteins that match a query. <br> \
  Example: query = ATF1.<br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  variants_genes_proteins: 'Retrieve genes and proteins associated with a variant matched by ID. <br> \
  Example: variant_id = NC_000001.11:630556:T:C.<br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  genes_proteins_genes_proteins: 'Retrieve genes or proteins associated with either genes or proteins that match a query. <br> \
  Example: query = ATF1.<br> \
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
  Example: query = ENSP00000384707 or query = ENST00000663609. <br> \
  name = \'involved in\' or \'is located in\' or \'has the function\' <br> \
  inverse_name = \'has component\' or \'contains\' or \'is a function of\' <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  go_terms_annotations: 'Retrieve annotations associated with a GO term. <br> \
  Example: go_term_id = GO_1990590. <br> \
  name = \'involved in\' or \'is located in\' or \'has the function\' <br> \
  inverse_name = \'has component\' or \'contains\' or \'is a function of\' <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  coding_variants: 'Retrieve coding variants annotations. <br> \
  Example: name = OR4F5_ENST00000641515_p.Met1!_c.1A-C, <br> \
  id = OR4F5_ENST00000641515_p.Met1!_c.1A-C, <br> \
  hgvsp = p.Met1?, <br> \
  gene_name = SAMD11, <br> \
  protein_id = ENSP00000384707, <br> \
  protein_name = SAM11_HUMAN, <br> \
  amino_acid_position = 1 (range values are also available, e.g: range:0-2), <br> \
  transcript_id = ENST00000342066.<br> \
  The limit parameter controls the page size and can not exceed 25. <br> \
  Pagination is 0-based.',

  nearest_genes: 'Retrieve a list of human genes if region is in a coding variant. Otherwise, it returns the nearest human genes on each side. <br> \
  Example: region = chr1:11868-14409 or region = chr1:1157520-1158189.',

  variants_diseases: 'Retrieve diseases and genes associated with the query variant from ClinGen. <br> \
  Example: variant_id = NC_000012.12:102917129:T:C <br> \
  spdi = NC_000012.12:102917129:T:C, <br> \
  hgvs = NC_000012.12:g.102917130T>C, <br> \
  rsid = rs62514891, <br> \
  chr = chr12, <br> \
  assertion = Pathogenic, <br> \
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
  Example: gene_id = ENSG00000183840, <br> \
  hgnc_id = HGNC:4496, <br> \
  gene_name = GPR39, <br> \
  alias = ZnR. <br> \
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
  Example: phenotype ID = OBA_0000128, <br> \
  phenotype_name = protein stability, <br> \
  organism = Homo sapiens. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based. <br><br> \
  We currently do not support searching by id = GO_0003674 or name = molecular_function due to the very large number of matching edges (even with pagination). <br> \
  If you need this matching data, please contact us.',

  coding_variants_phenotypes: 'Retrieve phenotypes associated with the query coding variant. <br> \
  Example: coding_variant_name = XRCC2_ENST00000359321__NC_000007.14:g.152660700C-T_splicing, <br> \
  hgvsp = p.Ala103Cys, <br> \
  protein_name = XRCC2_HUMAN, <br> \
  gene_name: XRCC2, <br> \
  amino_acid_position: -1, <br> \
  transcript_id = ENST00000359321, <br> \
  organism = Homo sapiens. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  llm_query: 'Ask a question that interests you. This API is password protected.<br> \
  Set verbose = true to retrieve AQL and AQL results.<br> \
  Example: query = Tell me about the gene SAMD11.',

  files_fileset: 'Retrieve data about a specific dataset.<br> \
  Example: file_fileset_id = ENCFF094BVF,<br>\
  fileset_id = ENCSR997TVR,<br>\
  lab = jesse-engreitz,<br>\
  preferred_assay_title = DNase-seq,<br>\
  method = MPRA,<br>\
  donor_id = ENCDO000AAK,<br>\
  sample_term = EFO_0002784,<br>\
  sample_summary = GM12878,<br>\
  software = Distal regulation ENCODE-rE2G,<br>\
  class = prediction,<br>\
  source = ENCODE.<br>\
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  genes_coding_variants: 'Retrieve scores and predictions of associated coding variants for a gene.<br> \
  Example: gene_id = ENSG00000196584, <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  genes_coding_variants_all_scores: 'Retrieve a list of all numeric scores of associated coding variants for a gene and a dataset.<br> \
  Example: gene_id = ENSG00000165841, <br> \
  dataset = VAMP-seq',

  variants_biosamples: 'Retrieve data from STARR-seq for a given variant.<br> \
  Example: variant_id = NC_000001.11:14772:C:T.<br> \
  spdi = NC_000001.11:14772:C:T, <br> \
  hgvs = NC_000001.11:g.14773C>T, <br> \
  rsid = rs1234567890, <br> \
  chr = chr1, <br> \
  position = 15566, <br> \
  organism = Homo sapiens, <br> \
  method = STARR-seq. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  biosamples_variants: 'Retrieve data from STARR-seq for a given biosample.<br> \
  Example: biosample_id = EFO_0002067, <br> \
  biosample_name = k562, <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.'
}
