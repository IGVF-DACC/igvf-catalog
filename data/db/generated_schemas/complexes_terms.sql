CREATE TABLE IF NOT EXISTS complexes_terms (
	term_name String,
	source String,
	source_url String,
	name String,
	inverse_name String,
	id String PRIMARY KEY,
	complexes_id String,
	ontology_terms_id String
);
