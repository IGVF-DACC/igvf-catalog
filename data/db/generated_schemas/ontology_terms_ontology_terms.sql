CREATE TABLE IF NOT EXISTS ontology_terms_ontology_terms (
	name String,
	inverse_name String,
	source String,
	source_url String,
	type String,
	type_uri String,
	id String PRIMARY KEY,
	ontology_terms_1_id String,
	ontology_terms_2_id String
);
