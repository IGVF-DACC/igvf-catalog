CREATE TABLE IF NOT EXISTS genes_mm_genes (
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	relationship LowCardinality(String),
	source LowCardinality(String),
	source_url LowCardinality(String),
	id String PRIMARY KEY,
	genes_id String,
	mm_genes_id String
);
