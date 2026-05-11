CREATE TABLE IF NOT EXISTS genes_structure (
	name String,
	source LowCardinality(String),
	source_url LowCardinality(String),
	chr LowCardinality(String),
	start UInt32,
	end UInt32,
	strand LowCardinality(String),
	type LowCardinality(String),
	gene_id String,
	gene_name String,
	transcript_id String,
	transcript_name String,
	exon_number String,
	exon_id String,
	version LowCardinality(String),
	organism LowCardinality(String),
	id String PRIMARY KEY
);
