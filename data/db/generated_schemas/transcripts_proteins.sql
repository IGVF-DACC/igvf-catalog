CREATE TABLE IF NOT EXISTS transcripts_proteins (
	source String,
	version String,
	source_url String,
	organism String,
	name String,
	inverse_name String,
	biological_process String,
	id String PRIMARY KEY,
	mm_transcripts_id String,
	transcripts_id String,
	proteins_id String
);
