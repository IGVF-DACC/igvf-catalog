CREATE TABLE IF NOT EXISTS variants_variants (
	chr LowCardinality(String),
	negated Bool,
	variants_1_id String,
	variants_2_id String,
	variants_1_rsid String,
	variants_2_rsid String,
	variants_1_base_pair String,
	variants_2_base_pair String,
	r2 Float32,
	d_prime Float32,
	ancestry LowCardinality(String),
	label LowCardinality(String),
	name LowCardinality(String),
	inverse_name LowCardinality(String),
	source LowCardinality(String),
	source_url LowCardinality(String)
)
ENGINE = MergeTree
ORDER BY (variants_1_id, ancestry, variants_2_id)
SETTINGS index_granularity = 8192;
