CREATE TABLE IF NOT EXISTS proteins (
	name String,
	source String,
	source_url String,
	MANE_Select Bool,
	protein_id String,
	version String,
	organism String,
	uniprot_collection String,
	uniprot_ids Array(String),
	uniprot_names Array(String),
	dbxrefs Array(JSON),
	uniprot_full_names Array(String),
	id String PRIMARY KEY
);
