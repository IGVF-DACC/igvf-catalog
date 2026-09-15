# MORF screen support files

`gencode.v43.metadata.RefSeq.gz` is the GENCODE v43 RefSeq cross-reference file, used by the MORF adapter for constructs without supplied ENST IDs. RefSeq accession versions are ignored; recovered transcript IDs must exist in the Catalog. Source: https://www.gencodegenes.org/human/release_43.html (RefSeq metadata).

`excluded_constructs.tsv` lists every skipped screen row for IGVFFI6734IWRB and IGVFFI6032GREJ using ORF reference IGVFFI2373SYJW and the saved development Catalog lookup in `MORF/validation/refseq_coverage.csv`. A construct appearing in both screens has one row per screen. Reasons follow adapter precedence: control construct, missing reference, no transcript, then missing log2FoldChange. Missing p-values alone do not cause exclusion.

This TSV is an input exclusion list: the adapter skips matching screen accession and normalized MORF_id pairs before transcript/gene mapping or statistics processing, and logs the listed reason. Review and update entries if source data or Catalog transcript availability changes; listed constructs remain excluded even if they become mappable. Unlisted rows still undergo normal adapter checks. Existing source ENSTs are retained without sequence validation.
