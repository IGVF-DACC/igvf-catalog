CREATE TABLE IF NOT EXISTS complexes (
	name String,
	source LowCardinality(String),
	source_url LowCardinality(String),
	alias Array(String),
	molecules Array(String),
	evidence_code LowCardinality(String),
	experimental_evidence Nullable(String),
	description String,
	complex_assembly LowCardinality(Nullable(String)),
	complex_source LowCardinality(String),
	reactome_xref Array(String),
	id String PRIMARY KEY
);
