CREATE TABLE IF NOT EXISTS donors (
	name String,
	source LowCardinality(String),
	source_url LowCardinality(String),
	sex LowCardinality(Nullable(String)),
	age Nullable(String),
	age_units LowCardinality(Nullable(String)),
	ethnicities Array(String),
	phenotypic_features Array(String),
	id String PRIMARY KEY
);
