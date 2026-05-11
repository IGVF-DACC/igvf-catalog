CREATE TABLE IF NOT EXISTS complexes_terms (
	term_name String,
	source LowCardinality(String),
	source_url LowCardinality(String),
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	id String PRIMARY KEY,
	complexes_id String,
	ontology_terms_id String
);
