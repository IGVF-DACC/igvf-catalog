CREATE TABLE IF NOT EXISTS variants_drugs_genes (
	name String,
	inverse_name String,
	gene_symbol String,
	source String,
	source_url String,
	id String PRIMARY KEY,
	variants_drugs_id String,
	genes_id String
);
