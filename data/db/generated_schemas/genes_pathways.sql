CREATE TABLE IF NOT EXISTS genes_pathways (
	source String,
	source_url String,
	name String,
	inverse_name String,
	organism String,
	id String PRIMARY KEY,
	genes_id String,
	pathways_id String
);
