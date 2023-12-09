export const descriptions = {
    regulatory_regions: 'Retrieve regulatory regions.<br> Example: region = chr1:1157520-1158189, biochemical_activity = CA, source = ENCODE_SCREEN (ccREs)',
    regulatory_regions_type: 'Retrieve regulatory regions by type.<br> Example: type = candidate_cis_regulatory_element',
    regulatory_regions_genes: 'Retrieve regulatory region - gene pairs by querying regulatory regions.<br> \
    Set verbose = true to retrieve full info on the regulatory regions.<br> Example: region = chr1:903900-904900, biochemical_activity = ENH',
    genes_regulatory_regions: 'Retrieve regulatory region - gene pairs by querying genes.<br> \
    Set verbose = true to retrieve full info on the genes.<br> Example: gene_id = ENSG00000187634, gene_name = SAMD11, region = chr1:923900-924900',
    genes: 'Retrieve genes.<br> Example: gene_name = ATF3, gene_region = chr1:212565300-212620800, alias = CKLF, gene_id = ENSG00000187642 (Ensembl ids)',
    genes_id: 'Retrieve genes by Ensembl id.<br> Example: id = ENSG00000187642',
    transcripts: 'Retrieve transcripts.<br> Example: region = chr20:9537369-9839076, transcript_type = protein_coding',
    transcripts_id: 'Retrieve transcripts by Ensembl id.<br> Example: id = ENST00000443707',
    proteins: 'Retrieve proteins.<br> Example: name = 1433B_HUMAN, dbxrefs = Orphanet:363611, protein_id = P49711',
    proteins_id: 'Retrieve proteins by Uniprot id.<br> Example: id = P49711',
    genes_transcripts: 'Retrieve transcripts from genes.<br> \
    Set verbose = true to retrieve full info on the transcripts.<br> Example: gene_name = ATF3, gene_region = chr1:212565300-212620800, alias = CKLF, gene_id = ENSG00000187642 (Ensembl ids)',
    genes_id_transcripts: 'Retrieve transcripts from Ensembl gene ids.<br> \
    Set verbose = true to retrieve full info on the transcripts.<br> Example: gene_id = ENSG00000230108',
    transcripts_genes: 'Retrieve genes from transcripts.<br> \
    Set verbose = true to retrieve full info on the genes.<br> Example: region = chr1:711800-740000, transcript_id = ENST00000443707 (Ensembl ID)',
    transcripts_id_genes: 'Retrieve genes from Ensembl transcript ids.<br> \
    Set verbose = true to retrieve full info on the genes.<br> Example: transcript_id = ENST00000443707',
    genes_proteins: 'Retrieve proteins from genes.<br> Example: gene_name = ATF3, gene_region = chr1:212565300-212620800, alias = CKLF, gene_id = ENSG00000170558 (Ensembl ID)',
    genes_id_proteins: 'Retrieve proteins from Ensembl gene ids.<br> Example: gene_id = ENSG00000230108',
    proteins_genes: 'Retrieve genes from proteins.<br> Example: name = CTCF_HUMAN, dbxrefs = Orphanet:363611, protein_id = P49711',
    proteins_id_genes: 'Retrieve genes from Uniprot protein ids.<br> Example: protein_id = P49711',
    transcripts_proteins: 'Retrieve proteins from transcripts.<br> \
    Set verbose = true to retrieve full info on the proteins.<br> Example: region = chr16:67562500-67640000, transcript_type = protein_coding, transcript_id = ENST00000401394 (Ensembl ID)',
    transcripts_id_proteins: 'Retrieve proteins from Ensembl transcript ids.<br> \
    Set verbose = true to retrieve full info on the proteins.<br> Example: transcript_id = ENST00000401394',
    proteins_transcripts: 'Retrieve transcripts from proteins.<br> \
    Set verbose = true to retrieve full info on the transcripts.<br> Example: name = CTCF_HUMAN, dbxrefs = Orphanet:363611, protein_id = P49711',
    proteins_id_transcripts: 'Retrieve transcripts from Uniprot protein ids.<br> \
    Set verbose = true to retrieve full info on the transcripts.<br> Example: protein_id = P49711',
    genes_genes: 'Retrieve coexpressed gene pairs from CoXPresdb.<br> The following parameters can be used to set thresholds on logit_score: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Example: gene_id = ENSG00000170558, logit_score = gt:0.1',
    variants: 'Retrieve genetic variants.<br> Example: region = chr1:1157520-1158189, funseq_description = coding (or noncoding), rsid = rs58658771',
    variants_id: 'Retrieve genetic variants by internal variant ids.<br> Example: id = 77e1ee142a7ed70fd9dd36513ef1b943fdba46269d76495a392cf863869a8dcb',
    variants_by_freq: 'Retrieve genetic variants within a genomic region by frequencies.<br> Example: region = chr3:186741137-186742238, source = 1000genomes, funseq_description = coding (or noncoding), minimum_maf: 0.1, maximum_maf:0.8',
    variants_variants: 'Retrieve genetic variants in linkage disequilibrium (LD).<br> The following parameters can be used to set thresholds on r2 and d_prime: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the variants.<br>  Example: variant_id = ec046cdcc26b8ee9e79f9db305b1e9d5a6bdaba2d2064176f9a4ea50007b1e9a, r2 = gte:0.8, d_prime = gt:0.9, ancestry = EUR',
    variants_genes_eqtl: 'Retrieve variant-gene pairs from GTEx eQTLs.<br> The following parameters can be used to set thresholds on p_value, beta, and slope: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the corresponding variants and genes.<br> Example: p_value = lte:0.01',
    variants_genes_sqtl: 'Retrieve variant-gene pairs from GTEx splice QTLs (sQTLs).<br> The following parameters can be used to set thresholds on p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the corresponding variants and genes.<br> Example: p_value = lte:0.01',
    variants_genes: 'Retrieve variant-gene pairs from GTEx eQTLs & sQTLs by internal variant ids. The following parameters can be used to set thresholds on p_value, beta, and slope: gt (>), gte (>=), lt (<), lte (<=), only.<br> \
    Set verbose = true to retrieve full info on the corresponding variants and genes.<br> Example: variant_id = 22f170e54c30a59e737beba20444f192201126f0b1415a7c9a106d1d01fe98d0, p_value = lte:0.01',
    genes_variants: 'Retrieve variant-gene pairs from GTEx eQTLs & sQTLs by Ensembl gene ids.<br> The following parameters can be used to set thresholds on p_value, beta, and slope: gt (>), gte (>=), lt (<), lte (<=), only.<br> \
    Set verbose = true to retrieve full info on the corresponding variants and genes.<br> Example: gene_id = ENSG00000187642, p_value = lte:0.01',
    variants_asb: 'Retrieve allele-specific transcription factor binding (ASB) variants from ADASTRA.<br> Example: variant_id = a182d43f6b87fe9bb0d5852d6a13e099ad04de51766fbcf0fec37d9d33146bd9',
    motifs: 'Retrieve transcription factor binding motifs from HOCOMOCO.<br> Example: name = STAT3_HUMAN',
    motifs_proteins: 'Retrieve proteins for motifs.<br> Set verbose = true to retrieve full info on the proteins.<br> Example: name = ATF1_HUMAN, source = HOCOMOCOv11',
    proteins_motifs: 'Retrieve motifs for proteins.<br> Set verbose = true to retrieve full info on the motifs.<br> Example: protein_id = P18846 (Uniprot ID), name = ATF1_HUMAN, full_name = Cyclic AMP-dependent transcription factor ATF-1, \
    dbxrefs = Ensembl:ENSP00000262053.3',
    phenotypes_id_variants: 'Retrieve variant-trait pairs from GWAS by phenotype ontology ids.<br> The following parameters can be used to set thresholds on p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the variants.<br> Example: phenotype_id = EFO_0007937, pmid = 30072576, p_value = lte:2e-10',
    phenotypes_variants: 'Retrieve variant-trait pairs from GWAS by phenotypes.<br> The following parameters can be used to set thresholds on p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the variants.<br> Example: term_id (phenotype ID) = EFO_0007937, term_name = blood protein measurement, p_value = lte:0.01',
    variants_id_phenotypes: 'Retrieve variant-trait pairs from GWAS by internal variant ids.<br> The following parameters can be used to set thresholds on p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the ontology terms of the traits.<br> Example: variant_id = 1f3e4afc831fff5a67f2401fb5dc7ef55b0e177f633b7fd88036962bacb925d9, pmid = 30595370, p_value = lte:0.01',
    variants_phenotypes: 'Retrieve variant-trait pairs from GWAS by variants.<br> The following parameters can be used to set thresholds on p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the ontology terms of the traits.<br> Example: region = chr1:1022580-1023580, rsid = rs2710889, pmid = 30595370, p_value = lte:0.01',
    diseases_genes: 'Retrieve disease-gene pairs from Orphanet by diseases.<br> \
    Set verbose = true to retrieve full info on the genes.<br> Example: term_name = cystic fibrosis or disease_id = Orphanet_586. Either term_name or disease_id are required.',
    diseases_id_genes: 'Retrieve disease-gene pairs from Orphanet by Orphanet ids.<br> \
    Set verbose = true to retrieve full info on the genes.<br> Example: disease_id = Orphanet_586',
    genes_diseases: 'Retrieve disease-gene pairs from Orphanet by genes.<br> \
    Set verbose = true to retrieve full info on the disease terms.<br> Example: gene_name = KCNN4, region = chr19:43764000-43784000, gene_type = protein_coding, alias = DHS2, gene_id = ENSG00000170558 (Ensembl ID)',
    genes_id_diseases: 'Retrieve disease-gene pairs from Orphanet by Ensembl gene ids.<br> \
    Set verbose = true to retrieve full info on the disease terms.<br> Example: gene_id = ENSG00000104783',
    ontology_terms: 'Retrieve ontology terms.<br> Example: term_id = Orphanet_101435, term_name = Rare genetic eye disease, source = EFO, subontology= molecular_function',
    ontology_terms_id: 'Retrieve ontology terms by ontology ids.<br> Example: term_id = EFO_1000960',
    ontology_terms_search: 'Retrieve ontology terms by searching term names.<br> Example: term = liver',
    go_mf: 'Retrieve the GO (Gene Ontology) terms for molecular functions.<br> Example: term_id = GO_0001545, term_name = primary ovarian follicle growth, primary ovarian follicle growth, primary ovarian follicle growth',
    go_cc: 'Retrieve the GO (Gene Ontology) terms for cellular components.<br> Example: term_id = GO_0001673, term_name = male germ cell nucleus, male germ cell nucleus, male germ cell nucleus',
    go_bp: 'Retrieve the GO (Gene Ontology) terms for biological processes.<br> Example: term_id = GO_0001664, term_name = G protein-coupled receptor binding, G protein-coupled receptor binding, G protein-coupled receptor binding',
    ontology_terms_children: 'Retrieve all child nodes of an ontology term.<br> Example: ontology_term_id = UBERON_0003661',
    ontology_terms_parents: 'Retrieve all parent nodes of an ontology term.<br> Example: ontology_term_id = UBERON_0014892',
    ontology_terms_transitive_closure: 'Retrieve all paths between two ontology terms (i.e. transitive closure).<br> Example: ontology_term_id_start = UBERON_0003663, ontology_term_id_end = UBERON_0014892',
    variants_proteins: 'Retrieve allele-specific transcription factor binding events from ADASTRA in any cell type by internal variant ids.<br> \
    Set verbose = true to retrieve full info on the transcription factors.<br> Example: variant_id = 027a180998e6da9822221181225654b628ecfe93fd7a23da92d1e4b9bc8db152',
    variants_id_proteins: 'Retrieve allele-specific transcription factor binding events from ADASTRA in any cell type by querying variants.<br> \
    Set verbose = true to retrieve full info on the transcription factors.<br> Example: region = chr20:3658940-3658960, rsid = rs6139176',
    proteins_id_variants: 'Retrieve allele-specific transcription factor binding events from ADASTRA in any cell type by Uniprot ids of the transcription factors.<br> \
    Set verbose = true to retrieve full info on the variants.<br> Example: protein_id = P49711',
    proteins_variants: 'Retrieve allele-specific transcription factor binding events from ADASTRA by querying transcription factors.<br> \
    Set verbose = true to retrieve full info on the variants.<br> Example: name = CTCF_HUMAN, dbxrefs = Ensembl:ENSP00000494538.1',
    proteins_id_biosamples: 'Retrieve allele-specific transcription factor binding events from ADASTRA in cell type-specific context by Uniprot ids of the transcription factors.<br> \
    Set verbose = true to retrieve full info on the ontology terms of the cell types.<br> Example: protein_id = P49711',
    proteins_biosamples: 'Retrieve allele-specific transcription factor binding events from ADASTRA in cell type-specific context by querying transcription factors.<br> \
    Set verbose = true to retrieve full info on the ontology terms of the cell types.<br> Example: name = CTCF_HUMAN, dbxrefs = Ensembl:ENSP00000494538.1',
    variants_id_biosamples: 'Retrieve allele-specific transcription factor binding events from ADASTRA in cell type-specific context by internal variant ids.<br> \
    Set verbose = true to retrieve full info on the variant-transcription factor pairs, and ontology terms of the cell types.<br> Example: variant_id = 027a180998e6da9822221181225654b628ecfe93fd7a23da92d1e4b9bc8db152',
    variants_biosamples: 'Retrieve allele-specific transcription factor binding events from ADASTRA in cell type-specific context by querying variants.<br> \
    Set verbose = true to retrieve full info on the variant-transcription factor pairs, and ontology terms of the cell types.<br> Example: region = chr20:3658940-3658960, rsid = rs6139176',
    biosamples_id_variants: 'Retrieve allele-specific transcription factor binding events from ADASTRA in cell type-specific context by ontology term ids of the cell types.<br> \
    Set verbose = true to retrieve full info on the variant-transcription factor pairs, and ontology terms of the cell types.<br> Example: term_id = EFO_0002067',
    biosamples_variants: 'Retrieve allele-specific transcription factor binding events from ADASTRA in cell type-specific context by querying cell types.<br> \
    Set verbose = true to retrieve full info on the variant-transcription factor pairs, and ontology terms of the cell types.<br> Example: term_id = EFO_0002067: term_name = K562',
    autocomplete: 'Autocomplete names for genes, proteins and ontology terms.<br> Example: term = ZNF, type = gene',
    complex: 'Retrieve complexes. Example: complex_id: CPX-11, name: SMAD1, description: phosphorylation',
    mm_regulatory_regions: 'Retrieve mouse regulatory regions.<br> Example: region = chr1:2035821-3036921, biochemical_activity = CA, source = ENCODE_SCREEN (ccREs)',
    drugs: 'Retrieve drugs (chemicals). Example: drug_id = PA448497 (chemical ids from pharmGKB), drug_name = aspirin',
    drugs_variants: 'Retrieve variants associated with the query drugs from pharmGKB.<br> Set verbose = true to retrieve full info on the variants.<br> \
    Example: drug_id = PA448497, drug_name = aspirin, pmid = 20824505, phenotype_categories = Toxicity',
    variants_drugs: 'Retrieve drugs associated with the query variants from pharmGKB.<br> Set verbose = true to retrieve full info on the drugs.<br> \
    Example: spdi = NC_000001.11:230714139:T:G, hgvs = NC_000001.11:g.230714140T>G, <br>variant_id = b8d8a33facd5b62cb7f1004ae38419b8d914082ea9b217bef008a6a7f0218687, rsid = rs5050 (at least one of those variant fields needs to be specified), <br> \
    the following filters on variants-drugs association can be combined for query: pmid = 20824505, phenotype_categories = Toxicity'
}
