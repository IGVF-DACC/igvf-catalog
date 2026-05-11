CREATE TABLE IF NOT EXISTS proteins (
	name String,
	source LowCardinality(String),
	source_url LowCardinality(String),
	MANE_Select Bool,
	protein_id String,
	version LowCardinality(String),
	organism LowCardinality(String),
	uniprot_collection LowCardinality(String),
	uniprot_ids Array(String),
	uniprot_names Array(String),
	dbxrefs Array(JSON),
	uniprot_full_names Array(String),
	id String PRIMARY KEY
);
