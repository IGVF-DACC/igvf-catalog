CREATE TABLE IF NOT EXISTS ontology_terms (
	name String,
	source String,
	source_url String,
	uri String,
	term_id String,
	description String,
	synonyms Array(Nullable(String)),
	subontology Nullable(String),
	subset Array(String),
	id String PRIMARY KEY
);
