CREATE TABLE IF NOT EXISTS diseases_genes (
	name String,
	inverse_name String,
	pmid Array(String),
	term_name String,
	gene_symbol String,
	association_type String,
	association_status String,
	source String,
	source_url String,
	id String PRIMARY KEY,
	ontology_terms_id String,
	genes_id String
);
