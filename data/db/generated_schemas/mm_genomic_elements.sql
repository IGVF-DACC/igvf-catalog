CREATE TABLE IF NOT EXISTS mm_genomic_elements (
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
	id String PRIMARY KEY
);
