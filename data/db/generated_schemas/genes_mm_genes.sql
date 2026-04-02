CREATE TABLE IF NOT EXISTS genes_mm_genes (
	name String,
	inverse_name String,
	relationship String,
	source String,
	source_url String,
	id String PRIMARY KEY,
	genes_id String,
	mm_genes_id String
);
