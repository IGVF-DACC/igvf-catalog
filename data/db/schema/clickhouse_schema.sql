SET allow_experimental_json_type = 1;

USE igvf;

CREATE TABLE IF NOT EXISTS variants_variants (
	chr String,
	ancestry String,
	negated boolean,
	variant_1_base_pair String,
	variant_2_base_pair String,
	variant_1_rsid String,
	variant_2_rsid String,
	r2 Float64,
	d_prime Float64,
	label String,
	name String,
	inverse_name String,
	source String,
	source_url String,
	variants_1_id String,
	variants_2_id String,
)
engine MergeTree order by (chr, ancestry);

CREATE TABLE IF NOT EXISTS variants (
    name String,
    chr String,
    pos Int64,
    rsid Array(String),
    ref String,
    alt String,
    qual String,
    spdi String,
    hgvs String,
    ca_id String,
    filter String,
    format String,
    source String,
    organism String,
    source_url String,
    annotations JSON,
    id String
)
ENGINE = ReplacingMergeTree()
PRIMARY KEY (spdi, id)
ORDER BY (spdi, id);

CREATE TABLE IF NOT EXISTS coding_variants (
	ref String,
	alt String,
	aapos Float64,
	name String,
	gene_name String,
	protein_name String,
	hgvsp String,
	hgvs String,
	refcodon String,
	codonpos String,
	transcript_id String,
	SIFT_score Float64,
	SIFT4G_score Float64,
	Polyphen2_HDIV_score Float64,
	Polyphen2_HVAR_score Float64,
	VEST4_score Float64,
	Mcap_score Float64,
	REVEL_score Float64,
	MutPred_score Float64,
	BayesDel_addAF_score Float64,
	BayesDel_noAF_score Float64,
	VARITY_R_score Float64,
	VARITY_ER_score Float64,
	VARITY_R_LOO_score Float64,
	VARITY_ER_LOO_score Float64,
	ESM1b_score Float64,
	EVE_score Float64,
	AlphaMissense_score Float64,
	CADD_raw_score Float64,
	source String,
	source_url String,
	id String PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS coding_variants_proteins (
	source String,
	source_url String,
  name String,
  inverse_name String,
	coding_variants_id String,
	proteins_id String
)
engine MergeTree order by (coding_variants_id, proteins_id);

CREATE TABLE IF NOT EXISTS variants_coding_variants (
	source String,
	source_url String,
  name String,
  inverse_name String,
	chr String,
	pos Int64,
	ref String,
	alt String,
	variants_id String,
	coding_variants_id String
)
engine MergeTree order by (variants_id, coding_variants_id);

CREATE TABLE IF NOT EXISTS genes (
	chr String,
	start UInt32,
	end UInt32,
	name String,
	gene_id String,
	gene_type String,
	hgnc String,
	entrez String,
	alias Array(String),
	source String,
	version String,
	source_url String,
	organism String,
	id String PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS transcripts (
	chr String,
	start UInt32,
	end UInt32,
	gene_name String,
	name String,
	transcript_id String,
	transcript_type String,
	source String,
	version String,
	source_url String,
	organism String,
	id String PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS ontology_terms (
	uri String,
	term_id String,
	name String,
	description String,
	synonyms Array(Nullable(String)),
	source String,
	subontology String,
	subset Array(String),
	id String PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS genes_transcripts (
	source String,
	version String,
	source_url String,
	name String,
	inverse_name String,
	biological_process String,
	organism String,
	id String PRIMARY KEY,
	transcripts_id String,
	genes_id String,
	mm_transcripts_id String,
	mm_genes_id String
);

CREATE TABLE IF NOT EXISTS genes_structure (
	id String,
	name String,
	chr String,
	start UInt32,
	end UInt32,
	strand String,
	type String,
	gene_id String,
	gene_name String,
	transcript_id String,
	transcript_name String,
	exon_number String,
	exon_id String,
	source String,
	version String,
	source_url String,
	organism String
)
engine MergeTree order by (chr, start, end);

CREATE TABLE IF NOT EXISTS mm_genes_structure (
	id String PRIMARY KEY,
	name String,
	chr String,
	start UInt32,
	end UInt32,
	strand String,
	type String,
	gene_id String,
	gene_name String,
	transcript_id String,
	transcript_name String,
	exon_number String,
	exon_id String,
	source String,
	version String,
	source_url String,
	organism String
);

CREATE TABLE IF NOT EXISTS transcripts_genes_structure (
	source String,
	version String,
	source_url String,
	name String,
	inverse_name String,
	organism String,
	transcripts_id String,
	genes_structure_id String
)
engine MergeTree order by (transcripts_id, genes_structure_id);

CREATE TABLE IF NOT EXISTS mm_transcripts_mm_genes_structure (
	source String,
	version String,
	source_url String,
	name String,
	inverse_name String,
	organism String,
	mm_transcripts_id String,
	mm_genes_structure_id String
)
engine MergeTree order by (mm_transcripts_id, mm_genes_structure_id);

CREATE TABLE IF NOT EXISTS ontology_terms_ontology_terms (
	name String,
	inverse_name String,
	source String,
	id String PRIMARY KEY,
	ontology_terms_1_id String,
	ontology_terms_2_id String
);

CREATE TABLE IF NOT EXISTS proteins (
	name String,
	full_name String,
	organism String,
	dbxrefs Array(String),
	source String,
	source_url String,
	id String PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS gene_products_terms (
	db String,
	gene_product_id String,
	gene_product_symbol String,
	qualifier Array(String),
	go_id String,
	db_reference Array(String),
	evidence String,
	with Array(String),
	aspect String,
	gene_product_name String,
	synonyms Array(String),
	gene_product_type String,
	taxon_id Array(String),
	date String,
	assigned_by String,
	annotation_extension String,
	gene_product_form_id String,
	source String,
	source_url String,
	organism String,
	name String,
	inverse_name String,
	id String PRIMARY KEY,
	ontology_terms_id String,
	proteins_id String,
	transcripts_id String
);

CREATE TABLE IF NOT EXISTS motifs (
	name String,
	tf_name String,
	source String,
	source_url String,
	pwm String,
	length UInt32,
	id String PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS motifs_proteins (
	source String,
	id String PRIMARY KEY,
	biological_process String,
	motifs_id String,
	proteins_id String,
	complexes_id String
);

CREATE TABLE IF NOT EXISTS mm_genes_mm_genes (
	detection_method String,
	detection_method_code String,
	interaction_type Array(String),
	interaction_type_code Array(String),
	confidence_value_biogrid Float64,
	confidence_value_intact Float64,
	source String,
	pmids Array(String),
	name String,
	inverse_name String,
	id String PRIMARY KEY,
	mm_genes_1_id String,
	mm_genes_2_id String
);

CREATE TABLE IF NOT EXISTS genes_pathways (
	name String,
	inverse_name String,
	source String,
	source_url String,
	organism String,
	id String PRIMARY KEY,
	genes_id String,
	pathways_id String
);

CREATE TABLE IF NOT EXISTS pathways (
	id_version String,
	name String,
	is_in_disease boolean,
	name_aliases Array(String),
	organism String,
	disease_ontology_terms Array(String),
	go_biological_process String,
	is_top_level_pathway boolean,
	source String,
	source_url String,
	id String PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS pathways_pathways (
	source String,
	source_url String,
	name String,
	inverse_name String,
	organism String,
	id String PRIMARY KEY,
	pathways_1_id String,
	pathways_2_id String
);

CREATE TABLE IF NOT EXISTS studies (
	name String,
	ancestry_initial String,
	ancestry_replication String,
	n_cases String,
	n_initial String,
	n_replication String,
	pmid String,
	pub_author String,
	pub_date String,
	pub_journal String,
	pub_title String,
	has_sumstats String,
	num_assoc_loci String,
	study_source String,
	trait_reported String,
	trait_efos String,
	trait_category String,
	source String,
	version String,
	id String PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS variants_phenotypes (
	equivalent_ontology_term String,
	source String,
	version String,
	id String PRIMARY KEY,
	variants_id String,
	ontology_terms_id String
);

CREATE TABLE IF NOT EXISTS variants_phenotypes_studies (
	lead_chrom String,
	lead_pos UInt32,
	lead_ref String,
	lead_alt String,
	phenotype_term String,
	direction String,
	beta Float64,
	beta_ci_lower Float64,
	beta_ci_upper Float64,
	odds_ratio Float64,
	oddsr_ci_lower Float64,
	oddsr_ci_upper Float64,
	p_val_mantissa Float64,
	p_val_exponent Float64,
	p_val Float64,
	log10pvalue Float64,
	tagged_variants Array(JSON),
	source String,
	version String,
	name String,
	inverse_name String,
	variants_phenotypes_id String,
	studies_id String
)
engine MergeTree order by (variants_phenotypes_id, studies_id);

CREATE TABLE IF NOT EXISTS drugs (
	name String,
	drug_ontology_terms Array(String),
	source String,
	source_url String,
	id String PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS variants_drugs (
	gene_symbol Array(String),
	pmid String,
	study_parameters Array(JSON),
	phenotype_categories Array(String),
	name String,
	inverse_name String,
	source String,
	source_url String,
	id String PRIMARY KEY,
	variants_id String,
	drugs_id String
);

CREATE TABLE IF NOT EXISTS variants_drugs_genes (
	gene_symbol String,
	source String,
	source_url String,
	name String,
	inverse_name String,
	id String PRIMARY KEY,
	variants_drugs_id String,
	genes_id String
);

CREATE TABLE IF NOT EXISTS transcripts_proteins (
	source String,
	source_url String,
	name String,
	inverse_name String,
	id String PRIMARY KEY,
	transcripts_id String,
	mm_transcripts_id String,
	proteins_id String
);

CREATE TABLE IF NOT EXISTS variants_proteins (
	rsid String,
	label String,
	source String,
	name String,
	inverse_name String,
	chr String,
	motif_fc String,
	motif_pos String,
	motif_orient String,
	motif_conc String,
	motif String,
	biological_process String,
	id String PRIMARY KEY,
	variants_id String,
	proteins_id String
);

CREATE TABLE IF NOT EXISTS variants_proteins_terms (
	es_mean_ref Float64,
	es_mean_alt Float64,
	fdrp_bh_ref Float64,
	fdrp_bh_alt Float64,
	biological_context String,
	source_url String,
	name String,
	inverse_name String,
	id String PRIMARY KEY,
	variants_proteins_id String,
	ontology_terms_id String
);

CREATE TABLE IF NOT EXISTS variants_genes (
	chr String,
	p_value Float64,
	log10pvalue Float64,
	effect_size Float64,
	sqrt_maf Float64,
	pval_nominal_threshold Float64,
	min_pval_nominal Float64,
	effect_size_se Float64,
	pval_beta Float64,
	intron_chr String,
	intron_start Float64,
	intron_end Float64,
	label String,
	name String,
	inverse_name String,
	biological_process String,
	biological_context String,
	source String,
	source_url String,
	id String PRIMARY KEY,
	variants_id String,
	genes_id String
);

CREATE TABLE IF NOT EXISTS variants_genes_terms (
	biological_context String,
	source String,
	source_url String,
	name String,
	inverse_name String,
	id String PRIMARY KEY,
	variants_genes_id String,
	ontology_terms_id String
);

CREATE TABLE IF NOT EXISTS proteins_proteins (
	detection_method String,
	detection_method_code String,
	interaction_type Array(String),
	interaction_type_code Array(String),
	confidence_value_biogrid Float64,
	confidence_value_intact Float64,
	source String,
	pmids Array(String),
	organism String,
	name String,
	inverse_name String,
	molecular_function String,
	id String PRIMARY KEY,
	proteins_1_id String,
	proteins_2_id String
);

CREATE TABLE IF NOT EXISTS genes_genes (
	z_score Float64,
	source String,
	source_url String,
	name String,
	inverse_name String,
	detection_method String,
	detection_method_code String,
	interaction_type Array(String),
	interaction_type_code Array(String),
	confidence_value_biogrid Float64,
	confidence_value_intact Float64,
	pmids Array(String),
	associated_process String,
	id String PRIMARY KEY,
	genes_1_id String,
	genes_2_id String
);

CREATE TABLE IF NOT EXISTS diseases_genes (
	pmid Array(String),
	name String,
	inverse_name String,
	term_name String,
	gene_symbol String,
	association_type String,
	association_status String,
	source String,
	source_url String,
	id String PRIMARY KEY,
	ontology_terms_id String,
	genes_id String
);

CREATE TABLE IF NOT EXISTS variants_diseases (
	gene_id String,
	assertion String,
	pmids Array(String),
	name String,
	inverse_name String,
	source String,
	source_url String,
	id String PRIMARY KEY,
	variants_id String,
	ontology_terms_id String
);

CREATE TABLE IF NOT EXISTS variants_diseases_genes (
	inheritance_mode String,
	name String,
	inverse_name String,
	source String,
	source_url String,
	id String PRIMARY KEY,
	variants_diseases_id String,
	genes_id String
);

CREATE TABLE IF NOT EXISTS genes_biosamples (
	biology_context String,
	model_id String,
	model_type String,
	cancer_term String,
	gene_dependency Float64,
	source String,
	source_url String,
	source_file String,
	name String,
	inverse_name String,
	id String PRIMARY KEY,
	genes_id String,
	ontology_terms_id String
);

CREATE TABLE IF NOT EXISTS complexes (
	name String,
	alias Array(String),
	molecules Array(String),
	evidence_code String,
	experimental_evidence String,
	description String,
	complex_assembly String,
	complex_source String,
	reactome_xref Array(String),
	source String,
	source_url String,
	id String PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS complexes_proteins (
	stoichiometry Int32,
	chain_id String,
	isoform_id String,
	number_of_paralogs Float64,
	paralogs Array(String),
	linked_features Array(JSON),
	source String,
	source_url String,
	id String PRIMARY KEY,
	complexes_id String,
	proteins_id String
);

CREATE TABLE IF NOT EXISTS complexes_terms (
	term_name String,
	source String,
	source_url String,
	name String,
	inverse_name String,
	id String PRIMARY KEY,
	complexes_id String,
	ontology_terms_id String
);

CREATE TABLE IF NOT EXISTS mm_genes (
	chr String,
	start UInt32,
	end UInt32,
	name String,
	gene_id String,
	gene_type String,
	mgi String,
	entrez String,
	alias Array(String),
	source String,
	version String,
	source_url String,
	organism String,
	id String PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS mm_transcripts (
	chr String,
	start UInt32,
	end UInt32,
	gene_name String,
	name String,
	transcript_id String,
	transcript_type String,
	source String,
	version String,
	source_url String,
	organism String,
	id String PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS mm_variants (
	chr String,
	pos UInt32,
	rsid Array(String),
	ref String,
	alt String,
	organism String,
	name String,
	spdi String,
	hgvs String,
	qual String,
	filter String,
	fi String,
	strain String,
	source String,
	source_url String,
	id String PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS genes_mm_genes (
	name String,
	inverse_name String,
	source String,
	source_url String,
	id String PRIMARY KEY,
	genes_id String,
	mm_genes_id String
);

CREATE TABLE IF NOT EXISTS coding_variants_phenotypes (
	abundance_score Float64,
	abundance_sd Float64,
	abundance_se Float64,
	ci_upper Float64,
	ci_lower Float64,
	abundance_Rep1 Float64,
	abundance_Rep2 Float64,
	abundance_Rep3 Float64,
	source String,
	source_url String,
	id String PRIMARY KEY,
	coding_variants_id String,
	ontology_terms_id String
);

CREATE TABLE IF NOT EXISTS donors (
	name String,
  donor_id String,
  sex String,
  ethnicity String,
  age String,
  age_units String,
  health_status String,
  source String,
  source_url String,
	id String PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS mm_genomic_elements (
	name String,
	chr String,
	start UInt32,
	end UInt32,
	source_annotation String,
	method_type String,
	type String,
	source String,
	source_url String,
	id String PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS variants_genomic_elements (
	label String,
	log10pvalue Float64,
	p_value Float64,
	beta Float64,
	source String,
	source_url String,
	biological_context String,
	biosample_term String,
	name String,
	method String,
	inverse_name String,
	id String PRIMARY KEY,
	variants_id String,
	genomic_elements_id String
);

CREATE TABLE IF NOT EXISTS genomic_elements_genes (
	score Float64,
	source String,
	source_url String,
	biological_context String,
	name String,
	inverse_name String,
	treatment_name Array(Nullable(String)),
	treatment_duration Array(Nullable(UInt32)),
	treatment_duration_units Array(Nullable(String)),
	treatment_amount Array(Nullable(Float32)),
	treatment_amount_units Array(Nullable(String)),
	treatment_notes String,
	id String PRIMARY KEY,
	genomic_elements_id String,
	genes_id String
);

CREATE TABLE IF NOT EXISTS genomic_elements (
	name String,
	chr String,
	start UInt32,
	end UInt32,
	method_type String,
	type String,
	source_annotation String,
	source String,
	source_url String,
	id String PRIMARY KEY,
	file_accession String
);

CREATE TABLE IF NOT EXISTS genomic_elements_biosamples (
	element_name String,
	strand String,
	activity_score Float64,
	bed_score Float64,
	DNA_count Float64,
	RNA_count Float64,
	source String,
	source_url String,
	name String,
	inverse_name String,
	id String PRIMARY KEY,
	genomic_elements_id String,
	ontology_terms_id String
);

CREATE TABLE IF NOT EXISTS variants_in_genes (
	gene_id String PRIMARY KEY,
	variant_ids Array(String)
);
