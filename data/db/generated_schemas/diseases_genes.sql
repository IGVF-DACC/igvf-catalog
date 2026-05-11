CREATE TABLE IF NOT EXISTS diseases_genes (
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	pmid Array(String),
	term_name String,
	gene_symbol String,
	association_type LowCardinality(String),
	association_status LowCardinality(String),
	source LowCardinality(String),
	source_url LowCardinality(String),
	id String PRIMARY KEY,
	ontology_terms_id String,
	genes_id String
);
