CREATE TABLE IF NOT EXISTS ontology_terms_ontology_terms (
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	source LowCardinality(String),
	source_url LowCardinality(String),
	type LowCardinality(String),
	type_uri LowCardinality(String),
	id String PRIMARY KEY,
	ontology_terms_1_id String,
	ontology_terms_2_id String
);
