CREATE TABLE IF NOT EXISTS variants_diseases (
	gene_id String,
	assertion String,
	pmids Array(String),
	name String,
	inverse_name String,
	source String,
	source_url String,
	id String PRIMARY KEY,
	variants_id String,
	ontology_terms_id String
);
