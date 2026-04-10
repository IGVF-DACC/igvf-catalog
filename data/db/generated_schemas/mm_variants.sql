CREATE TABLE IF NOT EXISTS mm_variants (
	name String,
	source String,
	source_url String,
	chr String,
	pos Float64,
	rsid Array(String),
	ref String,
	alt String,
	organism String,
	strain Array(String),
	qual String,
	filter Nullable(String),
	fi Float64,
	spdi String,
	hgvs String,
	id String PRIMARY KEY
);
