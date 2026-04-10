CREATE TABLE IF NOT EXISTS variants_coding_variants (
	source String,
	source_url String,
	name String,
	inverse_name String,
	chr String,
	pos Int64,
	ref String,
	alt String,
	label String,
	id String PRIMARY KEY,
	variants_id String,
	coding_variants_id String
);
