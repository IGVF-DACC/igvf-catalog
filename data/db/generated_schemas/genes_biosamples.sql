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
