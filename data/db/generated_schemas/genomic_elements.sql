CREATE TABLE IF NOT EXISTS genomic_elements (
	name String,
	source LowCardinality(String),
	source_url LowCardinality(String),
	chr LowCardinality(String),
	start UInt32,
	end UInt32,
	type String,
	method String,
	source_annotation String,
	files_filesets LowCardinality(String),
	simple_sample_summaries Array(String),
	treatments_term_ids Array(String),
	promoter_of String,
	id String PRIMARY KEY
);
