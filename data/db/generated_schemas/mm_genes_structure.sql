CREATE TABLE IF NOT EXISTS mm_genes_structure (
	name String,
	source String,
	source_url String,
	chr String,
	start Float64,
	end Float64,
	strand String,
	type String,
	gene_id String,
	gene_name String,
	transcript_id String,
	transcript_name String,
	exon_number String,
	exon_id String,
	version String,
	organism String,
	id String PRIMARY KEY
);
