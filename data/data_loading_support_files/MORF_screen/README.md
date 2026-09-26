# MORF screen support files

MORF now emits `genes_genes` edges with a `transcript` document link. The source gene comes from the ORF table's `ENSG_id`; blank gene IDs retain the name/synonym fallback. Every emitted transcript must exist and have exactly the source gene as its parent in `genes_transcripts`. Mismatches fail the load.

RefSeq-only constructs are resolved through `transcripts.refseq_transcript_ids`, ignoring RefSeq versions. This requires the transcript-node update from PR #894 (https://github.com/IGVF-DACC/igvf-catalog/pull/894) and a transcript reload. Until that data is available, RefSeq fallback fails with an explicit dependency error. There is no local-file fallback. The bundled RefSeq metadata is no longer used.

`excluded_constructs.tsv` lists every skipped screen row for IGVFFI6734IWRB and IGVFFI6032GREJ using ORF reference IGVFFI2373SYJW and the saved development Catalog lookup in `MORF/validation/refseq_coverage.csv`. A construct appearing in both screens has one row per screen. Reasons follow adapter precedence: control construct, missing reference, no transcript, then missing log2FoldChange. Missing p-values alone do not cause exclusion.

This TSV is an input exclusion list: the adapter skips matching screen accession and normalized MORF_id pairs before transcript/gene mapping or statistics processing, and logs the listed reason. Review and update entries if source data or Catalog transcript availability changes; listed constructs remain excluded even if they become mappable. Unlisted rows still undergo normal adapter checks. Existing source ENSTs are retained without sequence validation.
