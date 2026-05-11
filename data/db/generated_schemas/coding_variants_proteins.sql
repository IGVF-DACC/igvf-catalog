CREATE TABLE IF NOT EXISTS coding_variants_proteins (
	type String,
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	source LowCardinality(String),
	source_url LowCardinality(String),
	id String PRIMARY KEY,
	coding_variants_id String,
	proteins_id String
);
