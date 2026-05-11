CREATE TABLE IF NOT EXISTS mm_genomic_elements (
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
	id String PRIMARY KEY
);
