CREATE TABLE IF NOT EXISTS transcripts_genes_structure (
	source LowCardinality(String),
	version LowCardinality(String),
	source_url LowCardinality(String),
	organism LowCardinality(String),
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	id String PRIMARY KEY,
	transcripts_id String,
	genes_structure_id String
);
