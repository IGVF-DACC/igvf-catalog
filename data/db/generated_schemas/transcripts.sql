CREATE TABLE IF NOT EXISTS transcripts (
	name String,
	source LowCardinality(String),
	source_url LowCardinality(String),
	transcript_id String,
	transcript_type LowCardinality(String),
	chr LowCardinality(String),
	start UInt32,
	end UInt32,
	strand LowCardinality(String),
	gene_name String,
	MANE_Select Bool,
	version LowCardinality(String),
	organism LowCardinality(String),
	id String PRIMARY KEY
);
