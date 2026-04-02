CREATE TABLE IF NOT EXISTS mm_transcripts_mm_genes_structure (
	source String,
	version String,
	source_url String,
	organism String,
	name String,
	inverse_name String,
	id String PRIMARY KEY,
	mm_transcripts_id String,
	mm_genes_structure_id String
);
