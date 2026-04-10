CREATE TABLE IF NOT EXISTS genes_transcripts (
	source String,
	version String,
	source_url String,
	name String,
	inverse_name String,
	organism String,
	biological_process String,
	id String PRIMARY KEY,
	genes_id String,
	mm_genes_id String,
	mm_transcripts_id String,
	transcripts_id String
);
