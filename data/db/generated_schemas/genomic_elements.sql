CREATE TABLE IF NOT EXISTS genomic_elements (
	name String,
	source String,
	source_url String,
	chr String,
	start Float64,
	end Float64,
	type String,
	method String,
	source_annotation String,
	files_filesets String,
	simple_sample_summaries Array(String),
	treatments_term_ids Array(String),
	promoter_of String,
	id String PRIMARY KEY
);
