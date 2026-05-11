CREATE TABLE IF NOT EXISTS mm_transcripts_mm_genes_structure (
	source LowCardinality(String),
	version LowCardinality(String),
	source_url LowCardinality(String),
	organism LowCardinality(String),
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	id String PRIMARY KEY,
	mm_transcripts_id String,
	mm_genes_structure_id String
);
