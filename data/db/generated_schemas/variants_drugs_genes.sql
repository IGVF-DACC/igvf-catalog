CREATE TABLE IF NOT EXISTS variants_drugs_genes (
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	gene_symbol String,
	source LowCardinality(String),
	source_url LowCardinality(String),
	id String PRIMARY KEY,
	variants_drugs_id String,
	genes_id String
);
