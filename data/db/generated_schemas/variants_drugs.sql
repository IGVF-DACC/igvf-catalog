CREATE TABLE IF NOT EXISTS variants_drugs (
	gene_symbol Array(String),
	pmid String,
	study_parameters Array(String),
	phenotype_categories Array(String),
	name String,
	inverse_name String,
	source String,
	source_url String,
	id String PRIMARY KEY,
	variants_id String,
	drugs_id String
);
