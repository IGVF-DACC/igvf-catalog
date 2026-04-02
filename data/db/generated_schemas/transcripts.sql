CREATE TABLE IF NOT EXISTS transcripts (
	name String,
	source String,
	source_url String,
	transcript_id String,
	transcript_type String,
	chr String,
	start Float64,
	end Float64,
	strand String,
	gene_name String,
	MANE_Select Bool,
	version String,
	organism String,
	id String PRIMARY KEY
);
