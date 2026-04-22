CREATE TABLE IF NOT EXISTS variants_coding_variants (
	source LowCardinality(String),
	source_url LowCardinality(String),
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	chr LowCardinality(String),
	pos UInt32,
	ref LowCardinality(String),
	alt LowCardinality(String),
	id String PRIMARY KEY,
	variants_id String,
	coding_variants_id String
);
