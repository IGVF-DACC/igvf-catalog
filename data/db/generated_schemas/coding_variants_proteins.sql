CREATE TABLE IF NOT EXISTS coding_variants_proteins (
	type String,
	name String,
	inverse_name String,
	source String,
	source_url String,
	id String PRIMARY KEY,
	coding_variants_id String,
	proteins_id String
);
