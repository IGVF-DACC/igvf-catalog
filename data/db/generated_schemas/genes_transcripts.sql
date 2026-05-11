CREATE TABLE IF NOT EXISTS genes_transcripts (
	source LowCardinality(String),
	version LowCardinality(String),
	source_url LowCardinality(String),
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	organism LowCardinality(String),
	biological_process String,
	id String PRIMARY KEY,
	genes_id String,
	mm_genes_id String,
	mm_transcripts_id String,
	transcripts_id String
);
