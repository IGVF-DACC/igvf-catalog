export const descriptions = {
    regulatory_regions: 'Retrieve regulatory regions. Example: region = chr1:1157520-1158189, biochemical_activity = CA, source = ENCODE_SCREEN (ccREs)',
    regulatory_regions_type: 'Retrieve regulatory regions by type. Example: type = candidate_cis_regulatory_element',
    genes: 'Retrieve genes. Example: gene_name = ATF3, gene_region = chr1:212565300-212620800, alias = CKLF',
    genes_id: 'Retrieve genes by Ensembl id. Example: id = ENSG00000187642',
    transcripts: 'Retrieve transcripts. Example: region = chr20:9537369-9839076, transcript_type = protein_coding',
    transcripts_id: 'Retrieve transcripts by Ensembl id. Example: id = ENST00000443707',
    proteins: 'Retrieve proteins. Example: name = 1433B_HUMAN, dbxrefs = Orphanet:363611',
    proteins_id: 'Retrieve proteins by Uniprot id. Example: id = P49711',
    genes_transcripts: 'Retrieve transcripts from genes. Example: gene_name = ATF3, gene_region = chr1:212565300-212620800, alias = CKLF',
    genes_id_transcripts: 'Retrieve transcripts from Ensembl gene ids. Example: gene_id = ENSG00000230108',
    transcripts_genes: 'Retrieve genes from transcripts. Example: region = chr1:711800-740000',
    transcripts_id_genes: 'Retrieve genes from Ensembl transcript ids. Example: transcript_id = ENST00000443707',
    genes_proteins: 'Retrieve proteins from genes. Example: gene_name = ATF3, gene_region = chr1:212565300-212620800, alias = CKLF',
    genes_id_proteins: 'Retrieve proteins from Ensembl gene ids. Example: gene_id = ENSG00000230108',
    proteins_genes: 'Retrieve genes from proteins. Example: name = CTCF_HUMAN, dbxrefs = Orphanet:363611',
    proteins_id_genes: 'Retrieve genes from Uniprot protein ids. Example: protein_id = P49711',
    transcripts_proteins: 'Retrieve proteins from transcripts. Example: region = chr16:67562500-67640000, transcript_type = protein_coding',
    transcripts_id_proteins: 'Retrieve proteins from Ensembl transcript ids. Example: transcript_id = ENST00000401394',
    proteins_transcripts: 'Retrieve transcripts from proteins. Example: name = CTCF_HUMAN, dbxrefs = Orphanet:363611',
    proteins_id_transcripts: 'Retrieve transcripts from Uniprot protein ids. Example: protein_id = P49711',
    genes_genes: 'Retrieve coexpressed gene pairs from CoXPresdb. The following parameters can be used to set thresholds on logit_score: gt (>), gte (>=), lt (<), lte (<=). \
    Example: gene_id = ENSG00000170558, logit_score = gt:0.1',
    variants: 'Retrieve genetic variants. Example: region = chr1:1157520-1158189, funseq_description = coding (or noncoding), rsid = rs58658771',
    variants_id: 'Retrieve genetic variants by internal variant ids. Example: id = 77e1ee142a7ed70fd9dd36513ef1b943fdba46269d76495a392cf863869a8dcb',
    variants_by_freq: 'Retrieve genetic variants within a genomic region by frequencies. Example: region = chr3:186741137-186742238, source = 1000genomes, funseq_description = coding (or noncoding), min_alt_freq: 0.1, max_alt_freq:0.8',
    variants_variants: 'Retrieve genetic variants in linkage disequilibrium (LD). The following parameters can be used to set thresholds on r2 and d_prime: gt (>), gte (>=), lt (<), lte (<=). \
    Example: variant_id = ec046cdcc26b8ee9e79f9db305b1e9d5a6bdaba2d2064176f9a4ea50007b1e9a, r2 = gte:0.8, d_prime = gt:0.9, ancestry = EUR',
    variants_genes_eqtl: 'Retrieve variant-gene pairs from GTEx eQTLs. The following parameters can be used to set thresholds on p_value: gt (>), gte (>=), lt (<), lte (<=). Example: p_value = lte:0.01',
    variants_genes_sqtl: 'Retrieve variant-gene pairs from GTEx splice QTLs (sQTLs). The following parameters can be used to set thresholds on p_value: gt (>), gte (>=), lt (<), lte (<=). Example: p_value = lte:0.01',
    variants_id_genes: 'Retrieve variant-gene pairs from GTEx eQTLs & sQTLs by internal variant ids. The following parameters can be used to set thresholds on p_value: gt (>), gte (>=), lt (<), lte (<=). \
    Example: variant_id = 22f170e54c30a59e737beba20444f192201126f0b1415a7c9a106d1d01fe98d0, p_value = lte:0.01',
    genes_variants: 'Retrieve variant-gene pairs from GTEx eQTLs & sQTLs by Ensembl gene ids. The following parameters can be used to set thresholds on p_value: gt (>), gte (>=), lt (<), lte (<=). \
    Example: gene_id = ENSG00000187642, p_value = lte:0.01',
    variants_asb: 'Retrieve allele-specific transcription factor binding (ASB) variants from ADASTRA. Example: variant_id = a182d43f6b87fe9bb0d5852d6a13e099ad04de51766fbcf0fec37d9d33146bd9',
    motifs: 'Retrieve transcription factor binding motifs from HOCOMOCO. Example: name = STAT3_HUMAN',
    phenotypes_id_variants: 'Retrieve variant-trait pairs from GWAS by phenotype ontology ids. The following parameters can be used to set thresholds on p_value: gt (>), gte (>=), lt (<), lte (<=). \
    Example: phenotype_id = EFO_0007937, pmid = 30072576, p_value = lte:2e-10',
    phenotypes_variants: 'Retrieve variant-trait pairs from GWAS by phenotypes. The following parameters can be used to set thresholds on p_value: gt (>), gte (>=), lt (<), lte (<=). \
    Example: term_id = EFO_0007937, term_name = blood protein measurement, p_value = lte:0.01',
    variants_id_phenotypes: 'Retrieve variant-trait pairs from GWAS by internal variant ids. The following parameters can be used to set thresholds on p_value: gt (>), gte (>=), lt (<), lte (<=). \
    Example: variant_id = 1f3e4afc831fff5a67f2401fb5dc7ef55b0e177f633b7fd88036962bacb925d9, pmid = 30595370, p_value = lte:0.01',
    variants_phenotypes: 'Retrieve variant-trait pairs from GWAS by variants. The following parameters can be used to set thresholds on p_value: gt (>), gte (>=), lt (<), lte (<=). \
    Example: region = chr1:1022580-1023580, rsid = rs2710889, pmid = 30595370, p_value = lte:0.01',
    diseases_genes: 'Retrieve disease-gene pairs from Orphanet by diseases. Example: term_name = fibrosis',
    diseases_id_genes: 'Retrieve disease-gene pairs from Orphanet by Orphanet ids. Example: disease_id = Orphanet_586',
    genes_diseases: 'Retrieve disease-gene pairs from Orphanet by genes. Example: gene_name = KCNN4, region = chr19:43764000-43784000, gene_type = protein_coding, alias = DHS2',
    genes_id_diseases: 'Retrieve disease-gene pairs from Orphanet by Ensembl gene ids. Example: gene_id = ENSG00000104783',
    ontology_terms: 'Retrieve ontology terms. Example: term_id = Orphanet_101435, term_name = Rare genetic eye disease, source = EFO, subontology= molecular_function',
    ontology_terms_id: 'Retrieve ontology terms by ontology ids. Example: term_id = EFO_1000960',
    ontology_terms_search: 'Retrieve ontology terms by searching term names. Example: term = liver',
    go_mf: 'Retrieve the GO (Gene Ontology) terms for molecular functions. Example: term_id = GO_0001545, term_name = primary ovarian follicle growth, primary ovarian follicle growth, primary ovarian follicle growth',
    go_cc: 'Retrieve the GO (Gene Ontology) terms for cellular components. Example: term_id = GO_0001673, term_name = male germ cell nucleus, male germ cell nucleus, male germ cell nucleus',
    go_bp: 'Retrieve the GO (Gene Ontology) terms for biological processes. Example: term_id = GO_0001664, term_name = G protein-coupled receptor binding, G protein-coupled receptor binding, G protein-coupled receptor binding',
    ontology_terms_children: 'Retrieve all child nodes of an ontology term. Example: ontology_term_id = UBERON_0003661',
    ontology_terms_parents: 'Retrieve all parent nodes of an ontology term. Example: ontology_term_id = UBERON_0014892',
    ontology_terms_transitive_closure: 'Retrieve all paths between two ontology terms (i.e. transitive closure). Example: ontology_term_id_start = UBERON_0003663, ontology_term_id_end = UBERON_0014892',
    autocomplete: 'Autocomplete names for genes, proteins and ontology terms. Example: term = ZNF, type = gene'
}
