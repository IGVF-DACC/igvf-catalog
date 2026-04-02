CREATE TABLE IF NOT EXISTS motifs (
	name String,
	source String,
	source_url String,
	tf_name String,
	pwm Array(String),
	length Float64,
	baseline Float64,
	id String PRIMARY KEY
);
