CREATE TABLE IF NOT EXISTS transcripts_proteins (
	source LowCardinality(String),
	version LowCardinality(String),
	source_url LowCardinality(String),
	organism LowCardinality(String),
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	biological_process String,
	id String PRIMARY KEY,
	mm_transcripts_id String,
	transcripts_id String,
	proteins_id String
);
