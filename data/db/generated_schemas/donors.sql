CREATE TABLE IF NOT EXISTS donors (
	name String,
	source String,
	source_url String,
	sex Nullable(String),
	age Nullable(String),
	age_units Nullable(String),
	ethnicities Array(String),
	phenotypic_features Array(String),
	id String PRIMARY KEY
);
