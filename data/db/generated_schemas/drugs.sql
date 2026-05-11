CREATE TABLE IF NOT EXISTS drugs (
	name String,
	source LowCardinality(String),
	source_url LowCardinality(String),
	drug_ontology_terms Array(String),
	id String PRIMARY KEY
);
