CREATE TABLE IF NOT EXISTS complexes (
	name String,
	source String,
	source_url String,
	alias Array(String),
	molecules Array(String),
	evidence_code String,
	experimental_evidence Nullable(String),
	description String,
	complex_assembly Nullable(String),
	complex_source String,
	reactome_xref Array(String),
	id String PRIMARY KEY
);
