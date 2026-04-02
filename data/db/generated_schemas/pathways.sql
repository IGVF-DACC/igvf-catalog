CREATE TABLE IF NOT EXISTS pathways (
	name String,
	source String,
	source_url String,
	organism String,
	id_version String,
	is_in_disease Bool,
	name_aliases Array(String),
	is_top_level_pathway Bool,
	disease_ontology_terms Array(String),
	go_biological_process String,
	id String PRIMARY KEY
);
