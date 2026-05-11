CREATE TABLE IF NOT EXISTS motifs_proteins (
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	biological_process String,
	source LowCardinality(String),
	source_url LowCardinality(String),
	id String PRIMARY KEY,
	motifs_id String,
	proteins_id String
);
