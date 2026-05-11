CREATE TABLE IF NOT EXISTS variants_diseases_genes (
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	inheritance_mode LowCardinality(String),
	source LowCardinality(String),
	source_url LowCardinality(String),
	id String PRIMARY KEY,
	variants_diseases_id String,
	genes_id String
);
