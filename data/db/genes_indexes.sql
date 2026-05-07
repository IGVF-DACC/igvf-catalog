-- ===========================================================================
-- Genes table indexing primitives
-- ===========================================================================
-- Idempotent. Re-runnable after schema changes.
--
-- Adds:
--   1. Materialized lowercase columns for case-insensitive name/symbol/synonym
--      lookups (enables redesigned exact + fuzzy gene search in the router).
--   2. bloom_filter skip indexes on identifier and lowercase-name columns.
--   3. A (chr, start) projection for region intersect + nearest-gene queries.
--
-- See clickhouserewrite/design-decisions/ for the design rationale.
-- ===========================================================================

-- 1. Materialized lowercase columns -----------------------------------------
ALTER TABLE genes
  ADD COLUMN IF NOT EXISTS name_lower     String        MATERIALIZED lowerUTF8(name),
  ADD COLUMN IF NOT EXISTS symbol_lower   String        MATERIALIZED lowerUTF8(symbol),
  ADD COLUMN IF NOT EXISTS synonyms_lower Array(String) MATERIALIZED arrayMap(s -> lowerUTF8(s), synonyms);

-- Backfill: ADD COLUMN MATERIALIZED only computes for new inserts; existing
-- rows use the expression on read until materialized to disk.
ALTER TABLE genes MATERIALIZE COLUMN name_lower;
ALTER TABLE genes MATERIALIZE COLUMN symbol_lower;
ALTER TABLE genes MATERIALIZE COLUMN synonyms_lower;

-- 2. Skip indexes ------------------------------------------------------------
-- bloom_filter(0.01) sized for ~1% false positive at this granularity.
-- GRANULARITY 1 means one bloom per data granule (8192 rows; ~9 total at 68k).
ALTER TABLE genes
  ADD INDEX IF NOT EXISTS idx_gene_id        gene_id        TYPE bloom_filter(0.01) GRANULARITY 1,
  ADD INDEX IF NOT EXISTS idx_hgnc           hgnc           TYPE bloom_filter(0.01) GRANULARITY 1,
  ADD INDEX IF NOT EXISTS idx_entrez         entrez         TYPE bloom_filter(0.01) GRANULARITY 1,
  ADD INDEX IF NOT EXISTS idx_name_lower     name_lower     TYPE bloom_filter(0.01) GRANULARITY 1,
  ADD INDEX IF NOT EXISTS idx_symbol_lower   symbol_lower   TYPE bloom_filter(0.01) GRANULARITY 1,
  ADD INDEX IF NOT EXISTS idx_synonyms_lower synonyms_lower TYPE bloom_filter(0.01) GRANULARITY 1;

-- Backfill the skip indexes for existing parts.
ALTER TABLE genes MATERIALIZE INDEX idx_gene_id;
ALTER TABLE genes MATERIALIZE INDEX idx_hgnc;
ALTER TABLE genes MATERIALIZE INDEX idx_entrez;
ALTER TABLE genes MATERIALIZE INDEX idx_name_lower;
ALTER TABLE genes MATERIALIZE INDEX idx_symbol_lower;
ALTER TABLE genes MATERIALIZE INDEX idx_synonyms_lower;

-- 3. Region projection -------------------------------------------------------
-- (chr, start) ordering supports:
--   - region intersect: WHERE chr = ? AND end > a AND start < b
--   - nearest-left:    WHERE chr = ? AND end < pos ORDER BY end DESC LIMIT 1
--   - nearest-right:   WHERE chr = ? AND start > pos ORDER BY start LIMIT 1
-- Projection columns cover what nearestGeneSearch and region-intersect need
-- so the projection answers without falling back to the main table.
ALTER TABLE genes
  ADD PROJECTION IF NOT EXISTS proj_by_chr_start (
    SELECT id, gene_id, name, symbol, chr, start, end, gene_type, strand
    ORDER BY (chr, start)
  );

ALTER TABLE genes MATERIALIZE PROJECTION proj_by_chr_start;
