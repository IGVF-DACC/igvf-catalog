CREATE TABLE IF NOT EXISTS mm_variants (
	name String,
	source LowCardinality(String),
	source_url LowCardinality(String),
	chr LowCardinality(String),
	pos UInt32,
	rsid Array(String),
	ref String,
	alt String,
	organism LowCardinality(String),
	strain Array(String),
	qual Float32,
	filter Nullable(String),
	fi Float64,
	spdi String,
	hgvs String,
	id String PRIMARY KEY
);
