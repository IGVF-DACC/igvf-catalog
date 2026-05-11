CREATE TABLE IF NOT EXISTS complexes_proteins (
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	stoichiometry Int64,
	chain_id Nullable(String),
	isoform_id Nullable(String),
	number_of_paralogs Nullable(Int64),
	paralogs Array(String),
	linked_features Array(String),
	source LowCardinality(String),
	source_url LowCardinality(String),
	id String PRIMARY KEY,
	complexes_id String,
	proteins_id String
);
