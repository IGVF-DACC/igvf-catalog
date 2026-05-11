CREATE TABLE IF NOT EXISTS genes_biosamples (
	biology_context LowCardinality(String),
	model_id String,
	model_type LowCardinality(String),
	cancer_term String,
	gene_dependency Float64,
	source LowCardinality(String),
	source_url LowCardinality(String),
	source_file String,
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	id String PRIMARY KEY,
	genes_id String,
	ontology_terms_id String
);
