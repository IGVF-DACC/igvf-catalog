CREATE TABLE IF NOT EXISTS variants_diseases_genes (
	name String,
	inverse_name String,
	inheritance_mode String,
	source String,
	source_url String,
	id String PRIMARY KEY,
	variants_diseases_id String,
	genes_id String
);
