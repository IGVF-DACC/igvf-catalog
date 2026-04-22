CREATE TABLE IF NOT EXISTS variants_variants (
	chr LowCardinality(String),
	negated Bool,
	variant_1_base_pair String,
	variant_2_base_pair String,
	variant_1_rsid String,
	variant_2_rsid String,
	r2 Float64,
	d_prime Float64,
	ancestry LowCardinality(String),
	label String,
	name String,
	inverse_name String,
	source LowCardinality(String),
	source_url LowCardinality(String),
	id String PRIMARY KEY,
	variants_1_id String,
	variants_2_id String
);
