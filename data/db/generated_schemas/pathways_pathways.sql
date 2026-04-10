CREATE TABLE IF NOT EXISTS pathways_pathways (
	source String,
	source_url String,
	name String,
	inverse_name String,
	organism String,
	id String PRIMARY KEY,
	pathways_1_id String,
	pathways_2_id String
);
