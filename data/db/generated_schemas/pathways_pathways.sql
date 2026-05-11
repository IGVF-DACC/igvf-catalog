CREATE TABLE IF NOT EXISTS pathways_pathways (
	source LowCardinality(String),
	source_url LowCardinality(String),
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	organism LowCardinality(String),
	id String PRIMARY KEY,
	pathways_1_id String,
	pathways_2_id String
);
