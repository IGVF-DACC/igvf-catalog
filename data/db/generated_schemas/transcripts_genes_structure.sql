CREATE TABLE IF NOT EXISTS transcripts_genes_structure (
	source String,
	version String,
	source_url String,
	organism String,
	name String,
	inverse_name String,
	id String PRIMARY KEY,
	transcripts_id String,
	genes_structure_id String
);
