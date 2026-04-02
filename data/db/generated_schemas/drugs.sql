CREATE TABLE IF NOT EXISTS drugs (
	name String,
	source String,
	source_url String,
	drug_ontology_terms Array(String),
	id String PRIMARY KEY
);
