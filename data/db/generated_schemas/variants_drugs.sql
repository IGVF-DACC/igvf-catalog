CREATE TABLE IF NOT EXISTS variants_drugs (
	gene_symbol Array(String),
	pmid String,
	study_parameters Array(String),
	phenotype_categories Array(String),
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	source LowCardinality(String),
	source_url LowCardinality(String),
	id String PRIMARY KEY,
	variants_id String,
	drugs_id String
);
