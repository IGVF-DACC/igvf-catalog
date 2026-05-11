CREATE TABLE IF NOT EXISTS variants_diseases (
	gene_id String,
	assertion LowCardinality(String),
	pmids Array(String),
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	source LowCardinality(String),
	source_url LowCardinality(String),
	id String PRIMARY KEY,
	variants_id String,
	ontology_terms_id String
);
