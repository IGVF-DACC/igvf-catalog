CREATE TABLE IF NOT EXISTS genes_pathways (
	source LowCardinality(String),
	source_url LowCardinality(String),
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	organism LowCardinality(String),
	id String PRIMARY KEY,
	genes_id String,
	pathways_id String
);
