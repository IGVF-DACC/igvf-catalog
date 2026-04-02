CREATE TABLE IF NOT EXISTS motifs_proteins (
	name String,
	inverse_name String,
	biological_process String,
	source String,
	source_url String,
	id String PRIMARY KEY,
	motifs_id String,
	proteins_id String
);
