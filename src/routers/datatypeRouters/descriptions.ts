/* eslint-disable no-multi-str */
interface ExampleGroup {
  id: string
  label: string
  examples: Array<{
    label: string
    items: string[]
  }>
}

function examples (
  exampleGroups: ExampleGroup[],
  title = 'Examples by method',
  description = 'These examples are grouped by method; use the <code>method</code> filter to return data from a specific method.'
): string {
  const tabs = exampleGroups.map((example, index) => {
    const activeClass = index === 0 ? ' is-active' : ''
    return `<button class="method-example-tab${activeClass}" data-method-example-tab="${example.id}">${example.label}</button>`
  }).join(' ')

  const panels = exampleGroups.map((example, index) => {
    const activeClass = index === 0 ? ' is-active' : ''
    const exampleBlocks = example.examples.map((queryExample) => {
      const items = queryExample.items.map(item => `<li>${item}</li>`).join(' ')
      return `<div class="method-query-example"> <strong>${queryExample.label}</strong> <ul> ${items} </ul> </div>`
    }).join(' ')
    return `<div class="method-example-panel${activeClass}" data-method-example-panel="${example.id}"> <strong>${example.label}:</strong> ${exampleBlocks} </div>`
  }).join(' ')

  return `<div class="method-examples"> <strong>${title}</strong> <p class="method-example-description">${description}</p> <div class="method-example-tabs"> ${tabs} </div> ${panels} </div>`
}

export const descriptions = {
  genomic_elements: 'Retrieve genomic elements.<br> \
  Example: region = chr1:1157520-1158189, <br> \
  source_annotation = dELS: distal Enhancer-like signal, <br> \
  type = candidate cis regulatory element, <br> \
  files_fileset = IGVFFI5749WPVK, <br> \
  source = ENCODE. <br> \
  The limit parameter controls the page size and can not exceed 1000. <br> \
  Pagination is 0-based.',

  enhancer_gene_predictions:
    'Retrieve genomic elements and gene pairs by querying genomic elements.<br> \
    Set verbose = true to retrieve full info on the genes, genomic element and biosamples.<br> \
    ' + examples([
      {
        id: 'crispr-screen',
        label: 'CRISPR screen',
        examples: [
          {
            label: 'Single result',
            items: [
              'gene_id = ENSG00000055950',
              'gene_name = MRPL43',
              'hgnc_id = HGNC:14517',
              'alias = MRPL43',
              'method = CRISPR screen',
              'files_fileset = ENCFF968BZL'
            ]
          }
        ]
      },
      {
        id: 'encode-re2g',
        label: 'ENCODE-rE2G',
        examples: [
          {
            label: 'Single result',
            items: [
              'gene_id = ENSG00000055950',
              'gene_name = MRPL43',
              'hgnc_id = HGNC:14517',
              'alias = MRPL43',
              'method = ENCODE-rE2G',
              'files_fileset = ENCFF797EVP'
            ]
          }
        ]
      },
      {
        id: 'perturb-seq',
        label: 'Perturb-seq',
        examples: [
          {
            label: 'Single result',
            items: [
              'gene_id = ENSG00000055950',
              'gene_name = MRPL43',
              'hgnc_id = HGNC:14517',
              'alias = MRPL43',
              'method = Perturb-seq',
              'files_fileset = IGVFFI3069QCRA'
            ]
          }
        ]
      }
    ]),

  genes: 'Retrieve genes.<br> \
  Example: organism = Homo sapiens, <br> \
  name = SAMD1, <br> \
  region = chr1:212565300-212620800, <br> \
  synonym = CKLF, <br> \
  collection = ACMG73, <br> \
  study_set = MorPhiC, <br> \
  gene_id = ENSG00000187642 (Ensembl ids), <br> \
  gene_type = protein_coding, <br> \
  hgnc_id = HGNC:28208, <br> \
  entrez = ENTREZ:84808. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  genes_structure: 'Retrieve genes structure.<br> \
  you can filter by one of the four categories: gene, transcript, protein or region. <br> \
  Example: organism = Homo sapiens, <br> \
  region = chr1:212565300-212620800, <br> \
  gene_id = ENSG00000187642 (Ensembl ids), <br> \
  gene_name = ATF3, <br> \
  transcript_id = ENST00000443707 (Ensembl ids), <br> \
  type = exon, <br> \
  protein_id = ENSP00000305769, <br> \
  protein_name = SMAD1. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  transcripts: 'Retrieve transcripts. <br> \
  Example: region = chr20:9537369-9839076, <br> \
  transcript_type = protein_coding, <br> \
  transcript_id = ENST00000443707 (Ensembl ids), <br> \
  organism = Homo sapiens. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  proteins: 'Retrieve proteins.<br> \
  Protein IDs support the following formats: ENSP00000384707.1 or ENSP00000384707 (Ensembl IDs) or P49711-2 (Uniprot ids)<br> \
  Example: protein_id = ENSP00000384707, <br> \
  name = CTCF, <br> \
  uniprot_name = CTCF_HUMAN, <br> \
  uniprot_full_name = Transcriptional repressor CTCF, <br> \
  dbxrefs = P49711, <br> \
  organism = Homo sapiens. <br> \
  The limit parameter controls the page size and can not exceed 50. <br> \
  Pagination is 0-based.',

  genes_transcripts: 'Retrieve transcripts from genes.<br> \
    Set verbose = true to retrieve full info on the transcripts.<br> \
    At least one of these fields is required: gene_id, hgnc_id, gene_name, alias. <br> \
    Example: gene_name = ATF3, <br> \
    hgnc_id = HGNC:28208, <br> \
    alias = CKLF, <br> \
    organism = Homo sapiens, <br> \
    gene_id = ENSG00000187642 (Ensembl ids). <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based.',

  transcripts_genes: 'Retrieve genes from transcripts.<br> \
    Set verbose = true to retrieve full info on the genes.<br> \
    At least one of these fields is required: transcript_id, region or transcript_type. <br> \
    Example: transcript_id = ENST00000440782, <br> \
    region = chr1:711800-740000, <br> \
    transcript_type = protein_coding,<br> \
    organism = Homo sapiens, <br> \
    transcript_id = ENST00000443707 (Ensembl ID). <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based.',

  genes_proteins: 'Retrieve proteins from genes.<br> \
  Set verbose = true to retrieve full info on the proteins. <br> \
  At least one of these fields is required: gene_id, hgnc_id, gene_name, alias. <br> \
  Example: gene_name = ATF3, <br> \
  alias = CKLF, <br> \
  gene_id = ENSG00000170558 (Ensembl ID), <br> \
  hgnc_id = HGNC:13723. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  proteins_genes: 'Retrieve genes from proteins.<br> \
  Set verbose = true to retrieve full info on the genes.<br> \
  Protein IDs support the following formats: ENSP00000384707.1 or ENSP00000384707 (Ensembl IDs) or P49711-2 (Uniprot ids)<br> \
  Example: protein_id = ENSP00000384707, <br> \
  protein_name = CTCF, <br> \
  uniprot_name = CTCF_HUMAN, <br> \
  uniprot_full_name = Transcriptional repressor CTCF, <br> \
  dbxrefs = P49711, <br> \
  organism = Homo sapiens. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  transcripts_proteins: 'Retrieve proteins from transcripts.<br> \
    Set verbose = true to retrieve full info on the proteins.<br> \
    At least one of these fields is required: transcript_id, region or transcript_type. <br> \
    Example: transcript_id = ENST00000264010, <br> \
    region = chr16:67562500-67640000, <br> \
    transcript_type = protein_coding, <br> \
    organism = Homo sapiens, <br> \
    transcript_id = ENST00000401394 (Ensembl ID). <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based.',

  variants_variants_summary: 'Retrieve a summary of genetic variants in linkage disequilibrium (LD).<br> \
    Example: variant_id = NC_000001.11:954257:G:C,<br> \
    hgvs = NC_000011.10:g.9090011A>G,<br> \
    spdi = NC_000011.10:9090010:A:G,<br> \
    ca_id = CA10655063<br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based.',

  variants_genes_summary: 'Retrieve a summary of associated genes from GTEx eQTLs & splice QTLs by internal variant ids.<br> \
    Example: <br> \
    variant_id = NC_000001.11:40242002:G:A,<br> \
    spdi = NC_000001.11:40242002:G:A,<br> \
    hgvs = NC_000001.11:g.40242003G>A,<br> \
    ca_id = CA16051554,<br> \
    files_fileset = IGVFFI9602ILPC.',

  proteins_transcripts: 'Retrieve transcripts from proteins.<br> \
    Set verbose = true to retrieve full info on the transcripts.<br> \
    Protein IDs support the following formats: ENSP00000384707.1 or ENSP00000384707 (Ensembl IDs) or P49711-2 (Uniprot ids)<br> \
    Example: protein_name = CTCF, <br> \
    uniprot_name = CTCF_HUMAN, <br> \
    uniprot_full_name = Transcriptional repressor CTCF, <br> \
    dbxrefs = P49711, <br> \
    protein_id = ENSP00000384707, <br> \
    organism = Homo sapiens. <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based.',

  genes_genes:
    'Retrieve coexpressed gene pairs from CoXPresdb and genetic interactions from BioGRID. <br> \
    The following parameters can be used to set thresholds on z_score from CoXPresdb: gt (>), gte (>=), lt (<), lte (<=).<br> \
    At least one of these fields is required: gene_id, hgnc_id, gene_name, alias. <br> \
    Example: organism = Homo sapiens, <br> \
    source = COXPRESdb, <br> \
    interaction_type = dosage growth defect (sensu BioGRID), <br> \
    gene_id = ENSG00000121410, <br> \
    hgnc_id = HGNC:5, <br> \
    gene_name = A1BG, <br> \
    alias = HYST2477, <br> \
    associated_gene_id = ENSG00000269293, <br> \
    associated_hgnc_id = HGNC:48982, <br> \
    associated_gene_name = ZSCAN16-AS1, <br> \
    associated_alias = ZSCAN16 antisense RNA 1, <br> \
    z_score = gt:4, <br> \
    label = genetic interference, <br> \
    method = COXPRESdb, <br> \
    name = interacts with. <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based. <br> <br> \
    ' + examples([
      {
        id: 'biogrid',
        label: 'BioGRID',
        examples: [
          {
            label: 'Single result',
            items: [
              'gene_id = ENSG00000112592',
              'associated_gene_id = ENSG00000163132',
              'z_score = gte:0',
              'interaction_type = phenotypic suppression (sensu BioGRID)',
              'method = phenotypic suppression (sensu BioGRID)',
              'source = BioGRID',
              'name = interacts with',
              'organism = Homo sapiens'
            ]
          },
          {
            label: 'Group results',
            items: [
              'gene_id = ENSG00000112592',
              'source = BioGRID',
              'name = interacts with',
              'organism = Homo sapiens'
            ]
          }
        ]
      },
      {
        id: 'coxpresdb',
        label: 'COXPRESdb',
        examples: [
          {
            label: 'Single pair result',
            items: [
              'gene_id = ENSG00000153048',
              'associated_gene_id = ENSG00000233369',
              'z_score = lte:4',
              'method = COXPRESdb',
              'organism = Homo sapiens'
            ]
          },
          {
            label: 'Group results',
            items: [
              'gene_id = ENSG00000153048',
              'method = COXPRESdb',
              'name = coexpressed with',
              'organism = Homo sapiens'
            ]
          }
        ]
      }
    ],
    'Examples by source',
    'These examples are grouped by source; use the <code>source</code> filter to return data from a specific source.'
    ),

  variants: 'Retrieve genetic variants.<br> \
  Example: organism = Homo sapiens or Mus musculus.<br> \
  mouse_strain = CAST_EiJ (only for mouse variants). <br> \
  The examples below are specific to Homo sapiens: <br> \
  region = chr1:1157520-1158189 (maximum length: 10kb), <br> \
  GENCODE_category = coding or noncoding (only for human variants), <br> \
  rsid = rs58658771,  <br> \
  spdi = NC_000020.11:3658947:A:G, <br> \
  hgvs = NC_000020.11:g.3658948A>G, <br> \
  ca_id = CA739473472, <br> \
  variant_id = NC_000020.11:3658947:A:G. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  variants_summary: 'Retrieve genetic variants summary.<br> \
   Example: variant_id = NC_000020.11:3658947:A:G, <br> \
   spdi = NC_000020.11:3658947:A:G, <br> \
   hgvs = NC_000020.11:g.3658948A>G. <br> \
   ca_id = CA739473472',

  variants_alleles: 'Retrieve GNOMAD alleles for variants in a given region.<br> \
   Example: region = chr1:1157520-1158520 (maximum length: 10kb).<br> \
   Region limit: 1kb pairs.',

  variants_by_freq: 'Retrieve genetic variants within a genomic region by frequencies.<br> \
  Source is required. <br> \
   Example: region = chr3:186741137-186742238 (maximum length: 10kb), <br> \
   source = bravo_af, <br> \
   GENCODE_category = coding (or noncoding), <br> \
   spdi = NC_000003.12:186741142:G:A, <br> \
   hgvs = NC_000003.12:g.186741143G>A, <br> \
   rsid = rs1720801112, <br> \
   ca_id = CA739473472, <br> \
   minimum_af: 0, <br> \
   maximum_af:0.8. <br> \
   Pagination is 0-based.',

  variants_variants: 'Retrieve genetic variants in linkage disequilibrium (LD).<br> \
   The following parameters can be used to set thresholds on r2 and d_prime: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the variants.<br>  \
    At least one of these fields is required: variant_id, spdi, hgvs, rsid, ca_id, or region.<br> \
    Example: variant_id = NC_000011.10:9083634:A:T,<br> \
    spdi = NC_000011.10:9083634:A:T, <br> \
    hgvs = NC_000011.10:g.9083635A>T, <br> \
    rsid = rs60960132, <br> \
    ca_id = CA217534780, <br> \
    region = chr17:7166090-7166095 (maximum length: 10kb), <br> \
    r2 = gte:0.8, <br> \
    d_prime = gt:0.9, <br> \
    ancestry = EUR. <br> \
    The limit parameter controls the page size and can not exceed 500. <br> \
    Pagination is 0-based.',

  variants_genes:
    'Retrieve variant-gene pairs including eQTLs & splice QTLs from AFGR, eQTL Catalogue, and IGVF by variants.<br> \
    The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the corresponding variants and genes.<br> \
    At least one of these properties must be defined: spdi, hgvs, rsid, ca_id, variant_id, region, method, or files_filesets. <br> \
    The limit parameter controls the page size and can not exceed 500. <br> \
    Pagination is 0-based. <br> <br> \
    ' + examples([
      {
        id: 'eqtl',
        label: 'eQTL',
        examples: [
          {
            label: 'Single result',
            items: [
              'spdi = NC_000001.11:40241653:TGAA:TGAAATTGAA',
              'effect_size = gte:0.3',
              'method = eQTL, source = AFGR'
            ]
          },
          {
            label: 'Group results',
            items: [
              'region = chr1:40241650-40241759 (maximum length: 10kb)',
              'method = eQTL'
            ]
          }
        ]
      },
      {
        id: 'spliceqtl',
        label: 'spliceQTL',
        examples: [
          {
            label: 'Single result',
            items: [
              'spdi = NC_000001.11:898757:AAAAAA:AAAAAAA',
              'effect_size = gte:0.3',
              'method = spliceQTL'
            ]
          },
          {
            label: 'Group results',
            items: [
              'region = chr1:898750-898759 (maximum length: 10kb)',
              'method = spliceQTL'
            ]
          }
        ]
      },
      {
        id: 'variant-effects',
        label: 'Variant-EFFECTS',
        examples: [
          {
            label: 'Single result',
            items: [
              'spdi = NC_000010.11:79347741:AGGT:TCAG',
              'effect_size = lt:-0.6',
              'method = Variant-EFFECTS'
            ]
          },
          {
            label: 'Group results',
            items: [
              'region = chr10:79347740-79347749 (maximum length: 10kb)',
              'method = Variant-EFFECTS'
            ]
          }
        ]
      }
    ]),

  genes_variants:
    'Retrieve variant-gene pairs including eQTLs & splice QTLs from AFGR, eQTL Catalogue, and IGVF by Ensembl gene ids.<br> \
    The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the corresponding variants and genes.<br> \
    At least one of these properties must be defined: gene_id, hgnc_id, gene_name, region, alias, method, or files_fileset. <br> \
    The limit parameter controls the page size and can not exceed 500. <br> \
    Pagination is 0-based. <br> <br> \
    ' + examples([
      {
        id: 'eqtl',
        label: 'eQTL',
        examples: [
          {
            label: 'Single result',
            items: [
              'gene_id = ENSG00000187642',
              'hgnc_id = HGNC:28208',
              'gene_name = PERM1',
              'alias = PERM1',
              'method = eQTL, source = EBI, label = eQTL',
              'neg_log10_pvalue = gte:2, effect_size = lte:0.001',
              'biosample_term = UBERON_0001134, biological_context = muscle',
              'name = expression modulated by'
            ]
          },
          {
            label: 'Group results',
            items: [
              'gene_id = ENSG00000187642',
              'hgnc_id = HGNC:28208',
              'gene_name = PERM1',
              'alias = PERM1',
              'method = eQTL, source = EBI, label = eQTL',
              'neg_log10_pvalue = gte:2, effect_size = lte:0.001',
              'biosample_term = UBERON_0001134, biological_context = muscle',
              'name = expression modulated by'
            ]
          }
        ]
      },
      {
        id: 'spliceqtl',
        label: 'spliceQTL',
        examples: [
          {
            label: 'Single result',
            items: [
              'gene_id = ENSG00000188976',
              'hgnc_id = HGNC:24517',
              'gene_name = NOC2L',
              'alias = NOC2L',
              'method = spliceQTL, source = EBI, label = spliceQTL',
              'neg_log10_pvalue = gte:2, effect_size = lte:0.001',
              'biosample_term = UBERON_0008367, biological_context = breast',
              'name = splicing modulated by'
            ]
          },
          {
            label: 'Group results',
            items: [
              'gene_id = ENSG00000188976',
              'hgnc_id = HGNC:24517',
              'gene_name = NOC2L',
              'alias = NOC2L',
              'method = spliceQTL, source = EBI, label = spliceQTL',
              'neg_log10_pvalue = gte:2, effect_size = lte:0.001',
              'biosample_term = UBERON_0008367, biological_context = breast',
              'name = splicing modulated by'
            ]
          }
        ]
      },
      {
        id: 'variant-effects',
        label: 'Variant-EFFECTS',
        examples: [
          {
            label: 'Single result',
            items: [
              'gene_id = ENSG00000108179',
              'hgnc_id = HGNC:9259',
              'gene_name = PPIF',
              'alias = PPIF',
              'method = Variant-EFFECTS, source = IGVF, label = variant effect on gene expression',
              'files_fileset = IGVFFI4333XLOF',
              'name = expression modulated by'
            ]
          },
          {
            label: 'Group results',
            items: [
              'gene_id = ENSG00000108179',
              'hgnc_id = HGNC:9259',
              'gene_name = PPIF',
              'alias = PPIF',
              'method = Variant-EFFECTS, source = IGVF, label = variant effect on gene expression',
              'files_fileset = IGVFFI4333XLOF',
              'name = expression modulated by'
            ]
          }
        ]
      }
    ]),

  variants_region_summary: 'Retrieve a summary count of all methods reporting variants in a given region.<br> \
    Example: region = chr1:1157520-1158520 (maximum length: 10kb).',

  coding_variants_variants: 'Retrieve variants associated with a coding variant.<br> \
    Example: coding_variant_name = OR4F5_ENST00000641515_p.Gly30Ser_c.88G-A, <br> \
    hgvsp = p.Gly30Ser, <br> \
    The limit parameter controls the page size and can not exceed 500. <br> \
    Pagination is 0-based.',

  variants_coding_variants: 'Retrieve coding variants from dbSNFP associated with a variant.<br> \
    Example: variant_id = NC_000001.11:65564:A:T, <br> \
    spdi = NC_000001.11:65564:A:T, <br> \
    hgvs = NC_000001.11:g.65565A>T, <br> \
    ca_id = CA337806511, <br> \
    The limit parameter controls the page size and can not exceed 500.',

  coding_variants_phenotypes_count: 'Retrieve counts of coding variants associated with phenotypes.<br> \
    Example: gene_id = ENSG00000165841, <br> \
    files_fileset = IGVFFI6893ZOAA.',

  variants_phenotypes_summary_deprecated: 'DEPRECATED. Please use coding-variants/phenotypes/summary.<br> \
    Retrieve scores of variants associated with phenotypes. Via coding variants edges.<br> \
    Either variant_id or coding_variant_name are required. <br> \
    Example: variant_id = NC_000018.10:31546002:CA:GT, <br> \
    coding_variant_name = DSG2_ENST00000261590_p.Gln873Val_c.2617_2618delinsGT, <br> \
    files_fileset = IGVFFI6893ZOAA.',

  variants_phenotypes_summary: 'Retrieve scores of variants or coding_variants associated with phenotypes. Via coding variants edges.<br> \
    Either variant_id or coding_variant_name are required. <br> \
    Example: variant_id = NC_000018.10:31546002:CA:GT, <br> \
    coding_variant_name = DSG2_ENST00000261590_p.Gln873Val_c.2617_2618delinsGT, <br> \
    files_fileset = IGVFFI6893ZOAA.',

  motifs: 'Retrieve transcription factor binding motifs from HOCOMOCO.<br> \
  Example: tf_name = STAT3_HUMAN, <br> \
  source = HOCOMOCOv11. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  motifs_proteins: 'Retrieve proteins and complexes for motifs.<br> \
  Set verbose = true to retrieve full info on the proteins and complexes.<br> \
  Example: tf_name = ATF1_HUMAN, <br> \
  source = HOCOMOCOv11. <br> \
  The limit parameter controls the page size and can not exceed 1000. <br> \
  Pagination is 0-based.',

  proteins_motifs: 'Retrieve motifs for proteins.<br> \
  Set verbose = true to retrieve full info on the motifs.<br> \
  Protein IDs support the following formats: ENSP00000384707.1 or ENSP00000384707 (Ensembl IDs) or P49711-2 (Uniprot ids)<br> \
  Example: protein_id = ENSP00000384707, <br> \
  protein_name = CTCF, <br> \
  uniprot_name = CTCF_HUMAN, <br> \
  uniprot_full_name = Transcriptional repressor CTCF, <br> \
  dbxrefs = P49711,<br> \
  organism = Homo sapiens. <br> \
  The limit parameter controls the page size and can not exceed 1000. <br> \
  Pagination is 0-based.',

  phenotypes_variants:
    'Retrieve variant-trait pairs from GWAS, SGE, and cV2F by phenotypes.<br> \
    The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the studies.<br> \
    At least one of these fields is required: phenotype_id, phenotype_name, method, or files_fileset. <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based. <br> <br> \
    ' + examples([
      {
        id: 'gwas',
        label: 'GWAS',
        examples: [
          {
            label: 'Single result',
            items: [
              'phenotype_id = EFO_0010325',
              'phenotype_name = obsolete_precentral gyrus volume measurement',
              'method = GWAS, source = OpenTargets, label = GWAS, class = observed data',
              'neg_log10_pvalue = gte:5'
            ]
          },
          {
            label: 'Group results',
            items: [
              'phenotype_id = EFO_0010325',
              'phenotype_name = obsolete_precentral gyrus volume measurement',
              'method = GWAS, source = OpenTargets, label = GWAS, class = observed data',
              'neg_log10_pvalue = gte:5'
            ]
          }
        ]
      },
      {
        id: 'sge',
        label: 'SGE',
        examples: [
          {
            label: 'Single result',
            items: [
              'phenotype_id = NCIT_C16407',
              'phenotype_name = cell survival',
              'method = SGE, source = IGVF, label = protein variant effect, class = observed data',
              'files_fileset = IGVFFI3125FMNW'
            ]
          },
          {
            label: 'Group results',
            items: [
              'phenotype_id = NCIT_C16407',
              'phenotype_name = cell survival',
              'method = SGE, source = IGVF, label = protein variant effect, class = observed data',
              'files_fileset = IGVFFI3125FMNW'
            ]
          }
        ]
      },
      {
        id: 'cv2f',
        label: 'cV2F',
        examples: [
          {
            label: 'Single result',
            items: [
              'phenotype_id = GO_0003674',
              'phenotype_name = molecular_function',
              'method = cV2F, source = IGVF, label = predicted variant effect on phenotype, class = prediction',
              'files_fileset = IGVFFI3063JRLI'
            ]
          },
          {
            label: 'Group results',
            items: [
              'phenotype_id = GO_0003674',
              'phenotype_name = molecular_function',
              'method = cV2F, source = IGVF, label = predicted variant effect on phenotype, class = prediction',
              'files_fileset = IGVFFI3063JRLI'
            ]
          }
        ]
      }
    ]),

  variants_phenotypes:
    'Retrieve variant-trait pairs from GWAS, SGE, and cV2F by variants.<br> \
    Filters on phenotype ontology id can be used together.<br> \
    The following parameters can be used to set thresholds on -log10 p_value: gt (>), gte (>=), lt (<), lte (<=).<br> \
    Set verbose = true to retrieve full info on the studies.<br> \
    At least one of these fields is required: variant_id, spdi, hgvs, rsid, ca_id, region, method, or files_fileset. <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based. <br> <br> \
    ' + examples([
      {
        id: 'gwas',
        label: 'GWAS',
        examples: [
          {
            label: 'Single result',
            items: [
              'spdi = NC_000001.11:5277210:G:A',
              'neg_log10_pvalue = gte:5',
              'method = GWAS'
            ]
          },
          {
            label: 'Group results',
            items: [
              'region = chr1:5277208-5277214',
              'neg_log10_pvalue = gte:5',
              'method = GWAS, source = OpenTargets, label = GWAS, class = observed data'
            ]
          }
        ]
      },
      {
        id: 'sge',
        label: 'SGE',
        examples: [
          {
            label: 'Single result',
            items: [
              'variant_id = NC_000007.14:152660654:T:A',
              'spdi = NC_000007.14:152660654:T:A',
              'hgvs = NC_000007.14:g.152660655T>A',
              'region = chr7:152660650-152660658',
              'phenotype_id = NCIT_C16407',
              'method = SGE, source = IGVF, label = protein variant effect, class = observed data',
              'files_fileset = IGVFFI1361XVSO'
            ]
          },
          {
            label: 'Group results',
            items: [
              'variant_id = NC_000007.14:152660654:T:A',
              'spdi = NC_000007.14:152660654:T:A',
              'hgvs = NC_000007.14:g.152660655T>A',
              'region = chr7:152660650-152660658',
              'phenotype_id = NCIT_C16407',
              'method = SGE, source = IGVF, label = protein variant effect, class = observed data',
              'files_fileset = IGVFFI1361XVSO'
            ]
          }
        ]
      },
      {
        id: 'cv2f',
        label: 'cV2F',
        examples: [
          {
            label: 'Single result',
            items: [
              'variant_id = NC_000001.11:91420:T:C',
              'spdi = NC_000001.11:91420:T:C',
              'hgvs = NC_000001.11:g.91421T>C',
              'rsid = rs28619159',
              'ca_id = CA16735455',
              'region = chr1:91418-91424',
              'phenotype_id = GO_0003674',
              'method = cV2F, source = IGVF, label = predicted variant effect on phenotype, class = prediction',
              'files_fileset = IGVFFI0332UGDD'
            ]
          },
          {
            label: 'Group results',
            items: [
              'variant_id = NC_000001.11:91420:T:C',
              'spdi = NC_000001.11:91420:T:C',
              'hgvs = NC_000001.11:g.91421T>C',
              'rsid = rs28619159',
              'ca_id = CA16735455',
              'region = chr1:91418-91424',
              'phenotype_id = GO_0003674',
              'method = cV2F, source = IGVF, label = predicted variant effect on phenotype, class = prediction',
              'files_fileset = IGVFFI0332UGDD'
            ]
          }
        ]
      }
    ]),

  diseases_genes: 'Retrieve disease-gene pairs from Orphanet and GenCC by diseases.<br> \
    Set verbose = true to retrieve full info on the genes and diseases. <br> \
    Example: disease_name = fibrosis, <br> \
    disease_id = Orphanet_586, <br> \
    source = Orphanet. <br> \
    Either disease_name or disease_id are required. <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based.',

  genes_diseases: 'Retrieve disease-gene pairs from Orphanet, GenCC and ClinGen by genes.<br> \
    Set verbose = true to retrieve full info on the disease terms, and the variants associated with the disease from ClinGen. <br> \
    At least one of these fields is required: gene_id, hgnc_id, gene_name, alias. <br> \
    Example: gene_id = ENSG00000171759, <br> \
    gene_name = PAH, <br> \
    alias = PKU1, <br> \
    source = ClinGen, <br> \
    hgnc_id = HGNC:8582. <br> \
    The limit parameter controls the page size and can not exceed 25. <br> \
    Pagination is 0-based.',

  ontology_terms: 'Retrieve ontology terms.<br> \
  Example: term_id = Orphanet_101435, <br> \
  name = Rare genetic eye disease, <br> \
  synonyms = WTC11, <br> \
  source = EFO, <br> \
  subontology = molecular_function. <br> \
  The limit parameter controls the page size and can not exceed 1000. <br> \
  Pagination is 0-based.',

  ontology_terms_children: 'Retrieve all child nodes of an ontology term.<br> \
  Example: ontology_term_id = CHEBI_20857. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  ontology_terms_parents: 'Retrieve all parent nodes of an ontology term.<br> \
  Example: ontology_term_id = CHEBI_100001. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  ontology_terms_transitive_closure: 'Retrieve all paths between two ontology terms (i.e. transitive closure).<br> \
  Example: ontology_term_id_start = UBERON_0003663, <br> \
  ontology_term_id_end = UBERON_0014892',

  variants_proteins:
    'Retrieve allele-specific transcription factor binding events from ADASTRA in cell type-specific context, <br> \
    allele-specific transcription factor binding events from GVATdb, pQTL from UKB by querying variants, and predicted allele specific binding from SEMpl.<br> \
    Set verbose = true to retrieve full info on the variant-transcription factor pairs, and ontology terms of the cell types.<br> \
    At least one of these fields is required: variant_id, spdi, hgvs, rsid, ca_id, region, method, or files_fileset. <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based. <br> <br> \
    ' + examples([
      {
        id: 'adastra',
        label: 'ADASTRA',
        examples: [
          {
            label: 'query by variant identifier',
            items: [
              'variant_id = NC_000005.10:59317579:G:T',
              'method = ADASTRA'
            ]
          },
          {
            label: 'query by region',
            items: [
              'region = chr5:150575301-150575304',
              'method = ADASTRA'
            ]
          }
        ]
      },
      {
        id: 'gvatdb',
        label: 'GVATdb',
        examples: [
          {
            label: 'query by variant identifier',
            items: [
              'variant_id = NC_000010.11:112626979:C:T',
              'method = GVATdb'
            ]
          },
          {
            label: 'query by region',
            items: [
              'region = chr10:112626978-112626982',
              'method = GVATdb'
            ]
          }
        ]
      },
      {
        id: 'semvar',
        label: 'SEMVAR',
        examples: [
          {
            label: 'query by variant identifier',
            items: [
              'spdi = NC_000001.11:100091094:A:C',
              'method = SEMVAR'
            ]
          },
          {
            label: 'query by region',
            items: [
              'region = chr1:100091093-100091097',
              'method = SEMVAR'
            ]
          }
        ]
      },
      {
        id: 'pqtl',
        label: 'pQTL',
        examples: [
          {
            label: 'query by variant identifier',
            items: [
              'spdi = NC_000002.12:27508072:T:C',
              'method = pQTL'
            ]
          },
          {
            label: 'query by region',
            items: [
              'region = chr2:27508070-27508074',
              'method = pQTL'
            ]
          }
        ]
      }
    ]),

  proteins_variants:
    'Retrieve allele-specific transcription factor binding events from ADASTRA in cell type-specific context, <br> \
    allele-specific transcription factor binding events from GVATdb, pQTL from UKB by querying proteins, and predicted allele specific binding from SEMpl.<br> \
    Protein IDs support the following formats: ENSP00000384707.1 or ENSP00000384707 (Ensembl IDs) or P49711-2 (Uniprot ids).<br> \
    Set verbose = true to retrieve full info on the variant-transcription factor pairs, and the ontology terms of the cell types.<br> \
    At least one of these fields is required: protein_id, protein_name, uniprot_name, uniprot_full_name, dbxrefs, method, or files_fileset. <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based. <br> <br> \
    ' + examples([
      {
        id: 'adastra',
        label: 'ADASTRA',
        examples: [
          {
            label: 'Single result',
            items: [
              'protein_id = ENSP00000281043',
              'protein_name = MYCN',
              'uniprot_name = MYCN_HUMAN',
              'uniprot_full_name = N-myc proto-oncogene protein',
              'dbxrefs = MYCN',
              'method = ADASTRA, source = ADASTRA, label = allele-specific binding',
              'name = binding modulated by'
            ]
          },
          {
            label: 'Group results',
            items: [
              'protein_id = ENSP00000281043',
              'protein_name = MYCN',
              'uniprot_name = MYCN_HUMAN',
              'uniprot_full_name = N-myc proto-oncogene protein',
              'dbxrefs = MYCN',
              'method = ADASTRA, source = ADASTRA, label = allele-specific binding',
              'name = binding modulated by'
            ]
          }
        ]
      },
      {
        id: 'gvatdb',
        label: 'GVATdb',
        examples: [
          {
            label: 'Single result',
            items: [
              'protein_id = ENSP00000315417',
              'protein_name = ALX1',
              'uniprot_name = ALX1_HUMAN',
              'uniprot_full_name = ALX homeobox protein 1',
              'dbxrefs = ALX1',
              'method = GVATdb, source = GVATdb, label = allele-specific binding',
              'name = binding modulated by'
            ]
          },
          {
            label: 'Group results',
            items: [
              'protein_id = ENSP00000315417',
              'protein_name = ALX1',
              'uniprot_name = ALX1_HUMAN',
              'uniprot_full_name = ALX homeobox protein 1',
              'dbxrefs = ALX1',
              'method = GVATdb, source = GVATdb, label = allele-specific binding',
              'name = binding modulated by'
            ]
          }
        ]
      },
      {
        id: 'semvar',
        label: 'SEMVAR',
        examples: [
          {
            label: 'Single result',
            items: [
              'protein_id = ENSP00000351458',
              'protein_name = ELF2',
              'uniprot_name = ELF2_HUMAN',
              'uniprot_full_name = TS-related transcription factor Elf-2',
              'dbxrefs = ELF2',
              'method = SEMVAR, source = IGVF, label = predicted allele-specific binding',
              'files_fileset = IGVFFI0005WRQP',
              'name = binding modulated by'
            ]
          },
          {
            label: 'Group results',
            items: [
              'protein_id = ENSP00000351458',
              'protein_name = ELF2',
              'uniprot_name = ELF2_HUMAN',
              'uniprot_full_name = TS-related transcription factor Elf-2',
              'dbxrefs = ELF2',
              'method = SEMVAR, source = IGVF, label = predicted allele-specific binding',
              'files_fileset = IGVFFI0005WRQP',
              'name = binding modulated by'
            ]
          }
        ]
      },
      {
        id: 'pqtl',
        label: 'pQTL',
        examples: [
          {
            label: 'Single result',
            items: [
              'protein_id = ENSP00000263100',
              'protein_name = A1BG',
              'uniprot_name = A1BG_HUMAN',
              'uniprot_full_name = Alpha-1B-glycoprotein',
              'dbxrefs = A1BG',
              'method = pQTL, source = UKB, label = pQTL',
              'name = level associated with'
            ]
          },
          {
            label: 'Group results',
            items: [
              'protein_id = ENSP00000263100',
              'protein_name = A1BG',
              'uniprot_name = A1BG_HUMAN',
              'uniprot_full_name = Alpha-1B-glycoprotein',
              'dbxrefs = A1BG',
              'method = pQTL, source = UKB, label = pQTL',
              'name = level associated with'
            ]
          }
        ]
      }
    ]),

  autocomplete: 'Autocomplete names for genes and proteins based on prefix search.<br> \
  Example: term = TP53, <br> \
  Pagination is 0-based.',

  complex: 'Retrieve complexes.<br> \
  Example: complex_id = CPX-11, <br> \
  name = SMAD2, <br> \
  description = phosphorylation. <br> \
  Pagination is 0-based.',

  complexes_proteins: 'Retrieve protein participants for complexes. Each record includes complex and protein.<br> \
  Set verbose = true to retrieve full info on the complex and protein.<br> \
  Example: complex_id = CPX-9, <br> \
  complex_name = SMAD2, <br> \
  description = phosphorylation.<br> \
  The limit parameter controls the page size and can not exceed 50. <br> \
  Pagination is 0-based.',

  proteins_complexes: 'Retrieve complexes by querying from protein participants. Each record includes protein and complex.<br> \
  Set verbose = true to retrieve full info on the complexes.<br> \
  Protein IDs support the following formats: ENSP00000411322.1 or ENSP00000411322 (Ensembl IDs) or P67870 (Uniprot ids)<br> \
  Example: protein_id = ENSP00000411322.1, <br> \
  protein_name = CSNK2B, <br> \
  uniprot_name = CSK2B_HUMAN, <br> \
  uniprot_full_name = Casein kinase II subunit beta, <br> \
  dbxrefs = P67870. <br> \
  Pagination is 0-based.',

  drugs: 'Retrieve drugs (chemicals). <br> \
  Example: drug_id = PA448497 (chemical ids from pharmGKB), <br> \
  name = aspirin.<br> \
  The limit parameter controls the page size and can not exceed 1000. <br> \
  Pagination is 0-based.',

  drugs_variants: 'Retrieve variants associated with the query drugs from pharmGKB.<br> \
  Set verbose = true to retrieve full info on the variants. <br> \
  Either drug_id or drug_name is required. <br> \
  Example: drug_id = PA448497, <br> \
  drug_name = aspirin, <br> \
  pmid = 20824505, <br> \
  phenotype_categories = Toxicity. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  variants_drugs: 'Retrieve drugs associated with the query variants from pharmGKB.<br> \
  Set verbose = true to retrieve full info on the drugs.<br> \
  At least one of these fields is required: variant_id, spdi, hgvs, rsid, ca_id, or region. <br> \
  Example: variant_id = NC_000001.11:230714139:T:G, <br> \
  spdi = NC_000001.11:230714139:T:G, <br> \
  hgvs = NC_000001.11:g.230714140T>G, <br> \
  rsid = rs5050 (at least one of the variant fields needs to be specified), <br> \
  ca_id = CA10610220, <br> \
  region = chr3:186741137-186742238 (maximum length: 10kb), <br> \
  the following filters on variants-drugs association can be combined for query: <br> \
  pmid = 20824505, <br> \
  phenotype_categories = Toxicity. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  studies: 'Retrieve studies from GWAS. <br> \
  Example: study_id = GCST007798, <br> \
  pmid = 30929738. <br> \
  Pagination is 0-based.',

  variants_genomic_elements: 'Retrieve element gene predictions associated with a given variant.<br> \
  At least one of these fields is required: variant_id, spdi, hgvs, rsid, ca_id, or files_filesets. <br> \
  Example: variant_id = NC_000001.11:976214:A:G, <br> \
  hgvs = NC_000001.11:g.976215A>G,<br> \
  spdi = NC_000001.11:976214:A:G, <br> \
  rsid = rs7417106, <br> \
  ca_id = CA507079, <br> \
  files_filesets = ENCFF103XRK. <br> \
  The limit parameter controls the page size and can not exceed 300. <br> \
  Pagination is 0-based.',

  variants_genomic_elements_edge: 'Retrieve genomic elements associated with a given variant.<br> \
  Example: variant_id = NC_000001.11:976214:A:G, <br> \
  hgvs = NC_000001.11:g.976215A>G,<br> \
  spdi = NC_000001.11:976214:A:G, <br> \
  rsid = rs7417106, <br> \
  ca_id = CA507079, <br> \
  region = chr1:766254-766554, <br> \
  biosample_term = EFO_0002067, <br> \
  biological_context = K562, <br> \
  method = caQTL, <br> \
  files_fileset = ENCFF103XRK, <br> \
  The limit parameter controls the page size and can not exceed 300. <br> \
  Pagination is 0-based.',

  genomic_elements_variants_edge: 'Retrieve variants associated with genomic elements.<br> \
  Example: region = chr1:976210-976314, <br> \
  region_type = accessible dna elements, <br> \
  biosample_term = EFO_0002067, <br> \
  biological_context = K562, <br> \
  method = caQTL. <br> \
  The limit parameter controls the page size and can not exceed 300. <br> \
  Pagination is 0-based.',

  variants_genomic_elements_count: 'Retrieve counts of element gene predictions and cell types associated with a given variant.<br> \
  At least one of these fields is required: variant_id, spdi, hgvs, rsid, ca_id, or files_filesets. <br> \
  Example: variant_id = NC_000001.11:1628997:GGG:GG,<br> \
  hgvs = NC_000001.11:g.1629000del,<br> \
  spdi = NC_000001.11:1628997:GGG:GG,<br> \
  ca_id = CA1522823495,<br> \
  files_fileset = ENCFF705MLV.',

  proteins_proteins: 'Retrieve protein-protein interactions.<br> \
  Set verbose = true to retrieve full info on the proteins. <br> \
  Protein IDs support the following formats: ENSP00000384707.1 or ENSP00000384707 (Ensembl IDs) or P49711-2 (Uniprot ids)<br> \
  Example: protein_id = ENSP00000384707.1, <br> \
  protein_name = CTCF, <br> \
  uniprot_name = CTCF_HUMAN, <br> \
  uniprot_full_name = Transcriptional repressor CTCF, <br> \
  dbxrefs = P49711, <br> \
  detection_method = affinity chromatography technology, <br> \
  interaction_type = physical association, <br> \
  pmid = 28514442, <br> \
  associated_protein_id = ENSP00000428899, <br> \
  associated_protein_name = TNPO1, <br> \
  associated_uniprot_name = TNPO1_HUMAN, <br> \
  associated_uniprot_full_name = Transportin-1, <br> \
  associated_dbxrefs = DIP-29335N, <br> \
  label = affinity chromatography technology, <br> \
  method = physical association, <br> \
  source = BioGRID, <br> \
  organism = Homo sapiens. <br> \
  The limit parameter controls the page size and can not exceed 250. <br> \
  Pagination is 0-based.',

  genes_proteins_variants: 'Retrieve variants associated with genes or proteins that match a query. <br> \
  Example: query = ATF1.<br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  variants_genes_proteins: 'Retrieve genes and proteins associated with a variant matched by ID. <br> \
  Example: variant_id = NC_000001.11:630556:T:C<br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  genes_proteins_genes_proteins: 'Retrieve genes or proteins associated with either genes or proteins that match a query. <br> \
  Example: query = ATF1.<br> \
  The limit parameter controls the page size of related items and can not exceed 100. <br> \
  Pagination is 0-based.',

  genomic_elements_biosamples: 'Retrieve MPRA experiments by querying positions of genomic elements. <br> \
  Set verbose = true to retrieve full info on the cell ontology terms. <br> \
  Example: region_type = tested elements, <br> \
  region = chr10:100038743-100038963. <br> \
  files_fileset = ENCFF475FKV,<br> \
  method = MPRA,<br> \
  source = IGVF. <br> \
  The limit parameter controls the page size and can not exceed 50. <br> \
  Pagination is 0-based.',

  biosamples_genomic_elements: 'Retrieve MPRA expriments by querying cell ontology terms. <br> \
  Set verbose = true to retrieve full info on the tested genomic elements. <br> \
  Example: biosample_name = hepg2, <br> \
  method = MPRA, <br> \
  source = IGVF, <br> \
  files_fileset = ENCFF475FKV. <br> \
  The limit parameter controls the page size and can not exceed 50. <br> \
  Pagination is 0-based.',

  cell_gene_genomic_elements: 'Retrieve predicted associated genes and cell types for a given variant. <br> \
  Example: variant_id = NC_000012.12:69248967:C:T,<br> \
  spdi = NC_000012.12:69248967:C:T, <br> \
  hgvs = NC_000012.12:g.69248968C>T,<br> \
  rsid = rs544450198,<br> \
  ca_id = CA10655063,<br> \
  region = chr1:1157520-1158189 (maximum length: 10kb).',

  annotations_go_terms: 'Retrieve GO terms from either proteins or transcripts. <br> \
  Example: query = ENSP00000384707, <br> \
  name = involved in<br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  go_terms_annotations: 'Retrieve annotations associated with a GO term. <br> \
  Example: go_term_id = GO_1990590, <br> \
  name = has component<br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  coding_variants: 'Retrieve coding variants annotations. <br> \
  Example: name = OR4F5_ENST00000641515_p.Met1!_c.1A-C, <br> \
  id = OR4F5_ENST00000641515_p.Met1!_c.1A-C, <br> \
  hgvsp = p.Met1?, <br> \
  gene_name = SAMD11, <br> \
  protein_id = ENSP00000384707, <br> \
  protein_name = SAM11_HUMAN, <br> \
  amino_acid_position = 1 (range values are also available, e.g: range:0-2), <br> \
  transcript_id = ENST00000342066.<br> \
  The limit parameter controls the page size and can not exceed 25. <br> \
  Pagination is 0-based.',

  nearest_genes: 'Retrieve a list of human genes if region is in a coding variant. Otherwise, it returns the nearest human genes on each side. <br> \
  Example: region = chr1:1157520-1158189 (maximum length: 10kb).',

  variants_diseases: 'Retrieve diseases and genes associated with the query variant from ClinGen. <br> \
  At least one of these fields is required: variant_id, spdi, hgvs, rsid, ca_id, or region. <br> \
  Example: variant_id = NC_000012.12:102917129:T:C <br> \
  spdi = NC_000012.12:102917129:T:C, <br> \
  hgvs = NC_000012.12:g.102917130T>C, <br> \
  rsid = rs62514891, <br> \
  ca_id = CA114360, <br> \
  chr = chr12, <br> \
  region = chr12:102866500-102866700 (maximum length: 10kb), <br> \
  assertion = Pathogenic, <br> \
  pmid = 2574002. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  diseases_variants: 'Retrieve variants and genes associated with the query disease from ClinGen. <br> \
  Either disease_id or disease_name is required. <br> \
  Example: disease_id = MONDO_0009861, <br> \
  disease_name = phenylketonuria, <br> \
  assertion = Pathogenic, <br> \
  pmid = 2574002. <br> \
  The limit parameter controls the page size and can not exceed 100. <br> \
  Pagination is 0-based.',

  pathways: 'Retrieve pathways from Reactome.<br> \
  Example: id = R-HSA-164843, <br> \
  name = 2-LTR circle formation, <br> \
  is_in_disease = true. <br> \
  name_aliases = 2-LTR circle formation, <br> \
  is_top_level_pathway = true. <br> \
  disease_ontology_terms = DOID_526, <br> \
  go_biological_process = GO_0006015. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  genes_pathways: 'Retrieve pathways from genes.<br> \
  Set verbose = true to retrieve full info on the pathways and genes. <br> \
  At least one of these fields is required: gene_id, hgnc_id, gene_name, alias. <br> \
  Example: gene_id = ENSG00000183840, <br> \
  hgnc_id = HGNC:4496, <br> \
  gene_name = GPR39, <br> \
  alias = ZnR. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  pathways_genes: 'Retrieve genes from pathways.<br> \
  Set verbose = true to retrieve full info on the genes. <br> \
  At least one of these fields is required: pathway_id, pathway_name, or name_aliases <br> \
  Example: pathway_id = R-HSA-164843, <br> \
  pathway_name = 2-LTR circle formation, <br> \
  name_aliases = 2-LTR circle formation, <br> \
  disease_ontology_terms = DOID_526, <br> \
  go_biological_process = GO_0006015. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  pathways_pathways: 'Retrieve related pathway pairs from Reactome. <br> \
  Set verbose = true to retrieve full info on the pathway pairs. <br> \
  At least one of these fields is required: pathway_id, pathway_name, or name_aliases. <br> \
  Example: pathway_id = R-HSA-164843, <br> \
  pathway_name = 2-LTR circle formation, <br> \
  name_aliases = 2-LTR circle formation, <br> \
  disease_ontology_terms = DOID_526, <br> \
  go_biological_process = GO_0006015. <br> \
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  phenotypes_coding_variants:
    'Retrieve coding variants associated with the query phenotype.<br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based. <br> <br> \
    ' + examples([
      {
        id: 'esm-1v',
        label: 'ESM-1v',
        examples: [
          {
            label: 'Single result',
            items: [
              'phenotype_id = GO_0003674',
              'phenotype_name = molecular_function',
              'method = ESM-1v',
              'files_fileset = IGVFFI8105TNNO'
            ]
          },
          {
            label: 'Group results',
            items: [
              'phenotype_id = GO_0003674',
              'phenotype_name = molecular_function',
              'method = ESM-1v',
              'files_fileset = IGVFFI8105TNNO'
            ]
          }
        ]
      },
      {
        id: 'mutpred2',
        label: 'MutPred2',
        examples: [
          {
            label: 'Single result',
            items: [
              'phenotype_id = GO_0003674',
              'phenotype_name = molecular_function',
              'method = MutPred2',
              'files_fileset = IGVFFI6893ZOAA'
            ]
          },
          {
            label: 'Group results',
            items: [
              'phenotype_id = GO_0003674',
              'phenotype_name = molecular_function',
              'method = MutPred2',
              'files_fileset = IGVFFI6893ZOAA'
            ]
          }
        ]
      },
      {
        id: 'sge',
        label: 'SGE',
        examples: [
          {
            label: 'Single result',
            items: [
              'phenotype_id = NCIT_C16407',
              'phenotype_name = cell survival',
              'method = SGE',
              'files_fileset = IGVFFI2810SLAX'
            ]
          },
          {
            label: 'Group results',
            items: [
              'phenotype_id = NCIT_C16407',
              'phenotype_name = cell survival',
              'method = SGE',
              'files_fileset = IGVFFI2810SLAX'
            ]
          }
        ]
      },
      {
        id: 'vamp-seq',
        label: 'VAMP-seq',
        examples: [
          {
            label: 'Single result',
            items: [
              'phenotype_id = OBA_0000128',
              'phenotype_name = protein stability',
              'method = VAMP-seq',
              'files_fileset = IGVFFI0629IIQU'
            ]
          },
          {
            label: 'Group results',
            items: [
              'phenotype_id = OBA_0000128',
              'phenotype_name = protein stability',
              'method = VAMP-seq',
              'files_fileset = IGVFFI0629IIQU'
            ]
          }
        ]
      }
    ]),

  coding_variants_phenotypes:
    'Retrieve phenotypes associated with the query coding variant.<br> \
    At least one of these fields is required: coding_variant_name, hgvsp, uniprot_name, gene_name, amino_acid_position, transcript_id, method, files_fileset. <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based. <br> <br> \
    ' + examples([
      {
        id: 'esm-1v',
        label: 'ESM-1v',
        examples: [
          {
            label: 'Single result',
            items: [
              'coding_variant_name = A1BG_ENST00000263100_p.Ala118Asn_c.352_353delinsAA',
              'hgvsp = p.Ala118Asn',
              'uniprot_name = A1BG_HUMAN',
              'gene_name = A1BG',
              'amino_acid_position = 118',
              'transcript_id = ENST00000263100',
              'method = ESM-1v',
              'files_fileset = IGVFFI8105TNNO'
            ]
          },
          {
            label: 'Group results',
            items: [
              'coding_variant_name = A1BG_ENST00000263100_p.Ala118Asn_c.352_353delinsAA',
              'hgvsp = p.Ala118Asn',
              'uniprot_name = A1BG_HUMAN',
              'gene_name = A1BG',
              'amino_acid_position = 118',
              'transcript_id = ENST00000263100',
              'method = ESM-1v',
              'files_fileset = IGVFFI8105TNNO'
            ]
          }
        ]
      },
      {
        id: 'mutpred2',
        label: 'MutPred2',
        examples: [
          {
            label: 'Single result',
            items: [
              'coding_variant_name = A1BG_ENST00000263100_p.Ala118Arg_c.352_353delinsCG',
              'hgvsp = p.Ala118Arg',
              'uniprot_name = A1BG_HUMAN',
              'gene_name = A1BG',
              'amino_acid_position = 118',
              'transcript_id = ENST00000263100',
              'method = MutPred2',
              'files_fileset = IGVFFI6893ZOAA'
            ]
          },
          {
            label: 'Group results',
            items: [
              'coding_variant_name = A1BG_ENST00000263100_p.Ala118Arg_c.352_353delinsCG',
              'hgvsp = p.Ala118Arg',
              'uniprot_name = A1BG_HUMAN',
              'gene_name = A1BG',
              'amino_acid_position = 118',
              'transcript_id = ENST00000263100',
              'method = MutPred2',
              'files_fileset = IGVFFI6893ZOAA'
            ]
          }
        ]
      },
      {
        id: 'sge',
        label: 'SGE',
        examples: [
          {
            label: 'Single result',
            items: [
              'coding_variant_name = BRCA2_ENST00000380152__NC_000013.11:g.32319075A-C_splicing',
              'uniprot_name = BRCA2_HUMAN',
              'gene_name = BRCA2',
              'amino_acid_position = -1',
              'transcript_id = ENST00000380152',
              'method = SGE',
              'files_fileset = IGVFFI2810SLAX'
            ]
          },
          {
            label: 'Group results',
            items: [
              'coding_variant_name = BRCA2_ENST00000380152__NC_000013.11:g.32319075A-C_splicing',
              'uniprot_name = BRCA2_HUMAN',
              'gene_name = BRCA2',
              'amino_acid_position = -1',
              'transcript_id = ENST00000380152',
              'method = SGE',
              'files_fileset = IGVFFI2810SLAX'
            ]
          }
        ]
      },
      {
        id: 'vamp-seq',
        label: 'VAMP-seq',
        examples: [
          {
            label: 'Single result',
            items: [
              'coding_variant_name = CYP2C19_ENST00000371321_p.Ala103=_c.309T-G',
              'hgvsp = p.Ala103=',
              'uniprot_name = CP2CJ_HUMAN',
              'gene_name = CYP2C19',
              'amino_acid_position = 103',
              'transcript_id = ENST00000371321',
              'method = VAMP-seq',
              'files_fileset = IGVFFI0629IIQU'
            ]
          },
          {
            label: 'Group results',
            items: [
              'coding_variant_name = CYP2C19_ENST00000371321_p.Ala103=_c.309T-G',
              'hgvsp = p.Ala103=',
              'uniprot_name = CP2CJ_HUMAN',
              'gene_name = CYP2C19',
              'amino_acid_position = 103',
              'transcript_id = ENST00000371321',
              'method = VAMP-seq',
              'files_fileset = IGVFFI0629IIQU'
            ]
          }
        ]
      }
    ]),

  llm_query: 'Ask a question that interests you. This API is password protected.<br> \
  Set verbose = true to retrieve AQL and AQL results.<br> \
  Example: query = Tell me about the gene SAMD11.',

  files_fileset: 'Retrieve data about a specific dataset.<br> \
  Example: file_fileset_id = ENCFF004PFU,<br>\
  fileset_id = ENCSR359DFW,<br>\
  lab = jesse-engreitz,<br>\
  preferred_assay_title = DNase-seq,<br>\
  method = MPRA,<br>\
  donor_id = ENCDO000AAK,<br>\
  sample_term = EFO_0002784,<br>\
  sample_summary = GM12878,<br>\
  software = Distal regulation ENCODE-rE2G,<br>\
  cell_annotation = mesodermal cell, <br>\
  class = prediction,<br>\
  source = ENCODE.<br>\
  The limit parameter controls the page size and can not exceed 500. <br> \
  Pagination is 0-based.',

  genes_coding_variants:
    'Retrieve scores and predictions of associated coding variants for one specific gene.<br> \
    At least one of these fields is required: gene_id, hgnc_id, gene_name, alias. <br> \
    The limit parameter controls the page size and can not exceed 500. <br> \
    Pagination is 0-based. <br> <br> \
    ' + examples([
      {
        id: 'esm-1v',
        label: 'ESM-1v',
        examples: [
          {
            label: 'Single result',
            items: [
              'gene_id = ENSG00000121410',
              'gene_name = A1BG',
              'hgnc_id = HGNC:5',
              'alias = A1BG',
              'method = ESM-1v',
              'files_fileset = IGVFFI8105TNNO'
            ]
          },
          {
            label: 'Group results',
            items: [
              'gene_id = ENSG00000121410',
              'gene_name = A1BG',
              'hgnc_id = HGNC:5',
              'alias = A1BG',
              'method = ESM-1v',
              'files_fileset = IGVFFI8105TNNO'
            ]
          }
        ]
      },
      {
        id: 'mutpred2',
        label: 'MutPred2',
        examples: [
          {
            label: 'Single result',
            items: [
              'gene_id = ENSG00000196584',
              'gene_name = XRCC2',
              'hgnc_id = HGNC:12829',
              'alias = FANCU',
              'method = MutPred2',
              'files_fileset = IGVFFI6893ZOAA'
            ]
          },
          {
            label: 'Group results',
            items: [
              'gene_id = ENSG00000196584',
              'gene_name = XRCC2',
              'hgnc_id = HGNC:12829',
              'alias = FANCU',
              'method = MutPred2',
              'files_fileset = IGVFFI6893ZOAA'
            ]
          }
        ]
      },
      {
        id: 'sge',
        label: 'SGE',
        examples: [
          {
            label: 'Single result',
            items: [
              'gene_id = ENSG00000139618',
              'gene_name = BRCA2',
              'hgnc_id = HGNC:1101',
              'alias = BRCA2',
              'method = SGE',
              'files_fileset = IGVFFI2810SLAX'
            ]
          },
          {
            label: 'Group results',
            items: [
              'gene_id = ENSG00000139618',
              'gene_name = BRCA2',
              'hgnc_id = HGNC:1101',
              'alias = BRCA2',
              'method = SGE',
              'files_fileset = IGVFFI2810SLAX'
            ]
          }
        ]
      },
      {
        id: 'vamp-seq',
        label: 'VAMP-seq',
        examples: [
          {
            label: 'Single result',
            items: [
              'gene_id = ENSG00000165841',
              'gene_name = CYP2C19',
              'hgnc_id = HGNC:2621',
              'alias = CYP2C19',
              'method = VAMP-seq'
            ]
          },
          {
            label: 'Group results',
            items: [
              'gene_id = ENSG00000165841',
              'gene_name = CYP2C19',
              'hgnc_id = HGNC:2621',
              'alias = CYP2C19',
              'method = VAMP-seq'
            ]
          }
        ]
      }
    ]),

  genes_coding_variants_all_scores: 'Retrieve a list of all numeric scores of associated coding variants for a gene and a dataset.<br> \
  Example: gene_id = ENSG00000165841, <br> \
  dataset = VAMP-seq',

  variants_biosamples:
    'Retrieve data from STARR-seq, BlueSTARR, and MPRA for a given variant.<br> \
    At least one of these fields is required: variant_id, spdi, hgvs, rsid, ca_id, region, method, or files_fileset. <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based. <br> <br> \
    ' + examples([
      {
        id: 'mpra',
        label: 'MPRA',
        examples: [
          {
            label: 'Single result',
            items: [
              'variant_id = NC_000001.11:1000161:C:A',
              'spdi = NC_000001.11:1000161:C:A',
              'hgvs = NC_000001.11:g.1000162C>A',
              'region = chr1:1000160-1000163 (maximum length: 10kb)',
              'method = MPRA',
              'files_fileset = IGVFFI4378PZYI',
              'element_id = MPRA_chr1_1000079_1000279_GRCh38_plus_IGVFFI7321WGMD',
              'significant = false'
            ]
          },
          {
            label: 'Group results',
            items: [
              'variant_id = NC_000001.11:1000161:C:A',
              'spdi = NC_000001.11:1000161:C:A',
              'hgvs = NC_000001.11:g.1000162C>A',
              'region = chr1:1000160-1000163 (maximum length: 10kb)',
              'method = MPRA',
              'files_fileset = IGVFFI4378PZYI',
              'element_id = MPRA_chr1_1000079_1000279_GRCh38_plus_IGVFFI7321WGMD',
              'significant = false'
            ]
          }
        ]
      },
      {
        id: 'starr-seq',
        label: 'STARR-seq',
        examples: [
          {
            label: 'Single result',
            items: [
              'variant_id = NC_000001.11:14772:C:T',
              'spdi = NC_000001.11:14772:C:T',
              'hgvs = NC_000001.11:g.14773C>T',
              'rsid = rs878915777',
              'ca_id = CA16718507',
              'region = chr1:14771-14775 (maximum length: 10kb)',
              'method = STARR-seq',
              'files_fileset = IGVFFI4012FKNC'
            ]
          },
          {
            label: 'Group results',
            items: [
              'variant_id = NC_000001.11:14772:C:T',
              'spdi = NC_000001.11:14772:C:T',
              'hgvs = NC_000001.11:g.14773C>T',
              'rsid = rs878915777',
              'ca_id = CA16718507',
              'region = chr1:14771-14775 (maximum length: 10kb)',
              'method = STARR-seq',
              'files_fileset = IGVFFI4012FKNC'
            ]
          }
        ]
      },
      {
        id: 'bluestarr',
        label: 'BlueSTARR',
        examples: [
          {
            label: 'Single result',
            items: [
              'variant_id = NC_000001.11:100003415:C:A',
              'spdi = NC_000001.11:100003415:C:A',
              'hgvs = NC_000001.11:g.100003416C>A',
              'rsid = rs1360128702',
              'ca_id = CA884414298',
              'region = chr1:100003414-100003418 (maximum length: 10kb)',
              'method = BlueSTARR',
              'files_fileset = IGVFFI0818FMCC'
            ]
          },
          {
            label: 'Group results',
            items: [
              'variant_id = NC_000001.11:100003415:C:A',
              'spdi = NC_000001.11:100003415:C:A',
              'hgvs = NC_000001.11:g.100003416C>A',
              'rsid = rs1360128702',
              'ca_id = CA884414298',
              'region = chr1:100003414-100003418 (maximum length: 10kb)',
              'method = BlueSTARR',
              'files_fileset = IGVFFI0818FMCC'
            ]
          }
        ]
      }
    ]),

  biosamples_variants:
    'Retrieve data from STARR-seq, BlueSTARR, and MPRA for a given biosample.<br> \
    At least one of these fields is required: biosample_id or biosample_name. <br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based. <br> <br> \
    ' + examples([
      {
        id: 'mpra',
        label: 'MPRA',
        examples: [
          {
            label: 'Single result',
            items: [
              'biosample_id = EFO_0001182',
              'biosample_name = hek293',
              'method = MPRA',
              'files_fileset = IGVFFI4378PZYI',
              'element_id = MPRA_chr1_1000079_1000279_GRCh38_plus_IGVFFI7321WGMD',
              'significant = true'
            ]
          },
          {
            label: 'Group results',
            items: [
              'biosample_id = EFO_0001182',
              'biosample_name = hek293',
              'method = MPRA',
              'files_fileset = IGVFFI4378PZYI',
              'element_id = MPRA_chr1_1000079_1000279_GRCh38_plus_IGVFFI7321WGMD',
              'significant = true'
            ]
          }
        ]
      },
      {
        id: 'starr-seq',
        label: 'STARR-seq',
        examples: [
          {
            label: 'Single result',
            items: [
              'biosample_id = EFO_0002067',
              'biosample_name = k562',
              'method = STARR-seq',
              'files_fileset = IGVFFI7903VFKP'
            ]
          },
          {
            label: 'Group results',
            items: [
              'biosample_id = EFO_0002067',
              'biosample_name = k562',
              'method = STARR-seq',
              'files_fileset = IGVFFI7903VFKP'
            ]
          }
        ]
      },
      {
        id: 'bluestarr',
        label: 'BlueSTARR',
        examples: [
          {
            label: 'Single result',
            items: [
              'biosample_id = EFO_0002067',
              'biosample_name = k562',
              'method = BlueSTARR',
              'files_fileset = IGVFFI1663LKVQ',
              'element_id = candidate_cis_regulatory_element_chr1_100004290_100004635_GRCh38_ENCFF420VPZ'
            ]
          },
          {
            label: 'Group results',
            items: [
              'biosample_id = EFO_0002067',
              'biosample_name = k562',
              'method = BlueSTARR',
              'files_fileset = IGVFFI1663LKVQ',
              'element_id = candidate_cis_regulatory_element_chr1_100004290_100004635_GRCh38_ENCFF420VPZ'
            ]
          }
        ]
      }
    ]),

  grn:
    'Retrieve regulatory or response genes for a given regulatory gene. The network is modeled as: (regulators) -> (responses).<br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based. <br> <br> \
    ' + examples([
      {
        id: 'crispr-screen',
        label: 'CRISPR screen',
        examples: [
          {
            label: 'Single result',
            items: [
              'regulator_gene_id = ENSG00000143190',
              'regulator_gene_name = POU2F1',
              'regulator_hgnc_id = HGNC:9212',
              'regulator_alias = OCT1',
              'response_gene_id = ENSG00000152284',
              'response_gene_name = TCF7L1',
              'response_hgnc_id = HGNC:11640',
              'response_alias = TCF3',
              'p_value = gte:0',
              'method = CRISPR screen'
            ]
          },
          {
            label: 'Group results',
            items: [
              'regulator_gene_id = ENSG00000143190',
              'regulator_gene_name = POU2F1',
              'regulator_hgnc_id = HGNC:9212',
              'regulator_alias = OCT1',
              'response_gene_id = ENSG00000152284',
              'response_gene_name = TCF7L1',
              'response_hgnc_id = HGNC:11640',
              'response_alias = TCF3',
              'p_value = gte:0',
              'method = CRISPR screen'
            ]
          }
        ]
      },
      {
        id: 'perturb-seq',
        label: 'Perturb-seq',
        examples: [
          {
            label: 'Single result',
            items: [
              'regulator_gene_id = ENSG00000143190',
              'regulator_gene_name = POU2F1',
              'regulator_hgnc_id = HGNC:9212',
              'regulator_alias = OCT1',
              'response_gene_id = ENSG00000123685',
              'response_gene_name = BATF3',
              'response_hgnc_id = HGNC:28915',
              'response_alias = BATF3',
              'p_value = gte:0',
              'method = Perturb-seq'
            ]
          },
          {
            label: 'Group results',
            items: [
              'regulator_gene_id = ENSG00000143190',
              'regulator_gene_name = POU2F1',
              'regulator_hgnc_id = HGNC:9212',
              'regulator_alias = OCT1',
              'response_gene_id = ENSG00000123685',
              'response_gene_name = BATF3',
              'response_hgnc_id = HGNC:28915',
              'response_alias = BATF3',
              'p_value = gte:0',
              'method = Perturb-seq'
            ]
          }
        ]
      }
    ]),

  genes_genomic_elements:
    'Retrieve genomic elements and gene pairs by querying genes.<br> \
    One of these fields is required: gene_id, hgnc_id, gene_name, alias, method, or files_fileset. <br> \
    Set verbose = true to retrieve full info on the genes and genomic element.<br> \
    The limit parameter controls the page size and can not exceed 500. <br> \
    Pagination is 0-based. <br> <br> \
    ' + examples([
      {
        id: 'crispr-screen',
        label: 'CRISPR screen',
        examples: [
          {
            label: 'Single result',
            items: [
              'gene_id = ENSG00000116198',
              'gene_name = CEP104',
              'hgnc_id = HGNC:24866',
              'alias = CEP104',
              'method = CRISPR screen, source = ENCODE',
              'files_fileset = ENCFF968BZL',
              'biosample_term = EFO_0002067, biological_context = K562'
            ]
          },
          {
            label: 'Group results',
            items: [
              'gene_id = ENSG00000116198',
              'gene_name = CEP104',
              'hgnc_id = HGNC:24866',
              'alias = CEP104',
              'method = CRISPR screen, source = ENCODE',
              'files_fileset = ENCFF968BZL',
              'biosample_term = EFO_0002067, biological_context = K562'
            ]
          }
        ]
      },
      {
        id: 'encode-re2g',
        label: 'ENCODE-rE2G',
        examples: [
          {
            label: 'Single result',
            items: [
              'gene_id = ENSG00000225880',
              'gene_name = LINC00115',
              'hgnc_id = HGNC:26211',
              'alias = LINC00115',
              'method = ENCODE-rE2G, source = ENCODE',
              'files_fileset = ENCFF425TLX',
              'biosample_term = EFO_0002330, biological_context = SJSA1'
            ]
          },
          {
            label: 'Group results',
            items: [
              'gene_id = ENSG00000225880',
              'gene_name = LINC00115',
              'hgnc_id = HGNC:26211',
              'alias = LINC00115',
              'method = ENCODE-rE2G, source = ENCODE',
              'files_fileset = ENCFF425TLX',
              'biosample_term = EFO_0002330, biological_context = SJSA1'
            ]
          }
        ]
      },
      {
        id: 'perturb-seq',
        label: 'Perturb-seq',
        examples: [
          {
            label: 'Single result',
            items: [
              'gene_id = ENSG00000123685',
              'gene_name = BATF3',
              'hgnc_id = HGNC:28915',
              'alias = BATF3',
              'method = Perturb-seq, source = IGVF',
              'files_fileset = IGVFFI3069QCRA',
              'biosample_term = CL_0000909, biological_context = CD8-positive, alpha-beta memory T cell'
            ]
          },
          {
            label: 'Group results',
            items: [
              'gene_id = ENSG00000123685',
              'gene_name = BATF3',
              'hgnc_id = HGNC:28915',
              'alias = BATF3',
              'method = Perturb-seq, source = IGVF',
              'files_fileset = IGVFFI3069QCRA',
              'biosample_term = CL_0000909, biological_context = CD8-positive, alpha-beta memory T cell'
            ]
          }
        ]
      }
    ]),

  genomic_elements_genes:
    'Retrieve genomic elements and gene pairs by querying genomic elements.<br> \
    At least one of these properties must be defined: region, files_fileset, or method. <br> \
    Set verbose = true to retrieve full info on the genes and genomic element.<br> \
    The limit parameter controls the page size and can not exceed 500. <br> \
    Pagination is 0-based. <br> <br> \
    ' + examples([
      {
        id: 'crispr-screen',
        label: 'CRISPR screen',
        examples: [
          {
            label: 'Single result',
            items: [
              'region = chr1:3774714-3775214 (maximum length: 10kb)',
              'source_annotation = enhancer',
              'region_type = tested elements',
              'method = CRISPR screen, source = ENCODE',
              'files_fileset = ENCFF968BZL',
              'biosample_term = EFO_0002067, biological_context = K562'
            ]
          },
          {
            label: 'Group results',
            items: [
              'region = chr1:3774714-3775214 (maximum length: 10kb)',
              'source_annotation = enhancer',
              'region_type = tested elements',
              'method = CRISPR screen, source = ENCODE',
              'files_fileset = ENCFF968BZL',
              'biosample_term = EFO_0002067, biological_context = K562'
            ]
          }
        ]
      },
      {
        id: 'encode-re2g',
        label: 'ENCODE-rE2G',
        examples: [
          {
            label: 'Single result',
            items: [
              'region = chr1:778465-778965 (maximum length: 10kb)',
              'method = ENCODE-rE2G, source = ENCODE',
              'files_fileset = ENCFF003BKC',
              'biosample_term = UBERON_0004539, biological_context = right kidney from ENCDO453STB'
            ]
          },
          {
            label: 'Group results',
            items: [
              'region = chr1:778465-778965 (maximum length: 10kb)',
              'method = ENCODE-rE2G, source = ENCODE',
              'files_fileset = ENCFF003BKC',
              'biosample_term = UBERON_0004539, biological_context = right kidney from ENCDO453STB'
            ]
          }
        ]
      },
      {
        id: 'perturb-seq',
        label: 'Perturb-seq',
        examples: [
          {
            label: 'Single result',
            items: [
              'region = chr1:212699339-212700840 (maximum length: 10kb)',
              'method = Perturb-seq, source = IGVF',
              'files_fileset = IGVFFI3069QCRA',
              'biosample_term = CL_0000909, biological_context = CD8-positive, alpha-beta memory T cell'
            ]
          },
          {
            label: 'Group results',
            items: [
              'region = chr1:212699339-212700840 (maximum length: 10kb)',
              'method = Perturb-seq, source = IGVF',
              'files_fileset = IGVFFI3069QCRA',
              'biosample_term = CL_0000909, biological_context = CD8-positive, alpha-beta memory T cell'
            ]
          }
        ]
      }
    ]),

  qtls:
    'Retrieve QTLs from gene, variant, or region.<br> \
    Define exactly one query type: gene (gene_id or gene_name), variant (variant_id, spdi, rsid, or ca_id), or region.<br> \
    The limit parameter controls the page size and can not exceed 100. <br> \
    Pagination is 0-based. <br> <br> \
    ' + examples([
      {
        id: 'eqtl',
        label: 'eQTL',
        examples: [
          {
            label: 'Single result',
            items: [
              'variant_id = NC_000001.11:40241653:TGAA:TGAAATTGAA',
              'spdi = NC_000001.11:40241653:TGAA:TGAAATTGAA',
              'rsid = rs79070333',
              'ca_id = CA21017128',
              'method = eQTL, source = AFGR',
              'biological_context = lymphoblastoid cell line'
            ]
          },
          {
            label: 'Group results',
            items: [
              'variant_id = NC_000001.11:40241653:TGAA:TGAAATTGAA',
              'spdi = NC_000001.11:40241653:TGAA:TGAAATTGAA',
              'rsid = rs79070333',
              'ca_id = CA21017128',
              'method = eQTL, source = AFGR',
              'biological_context = lymphoblastoid cell line'
            ]
          }
        ]
      },
      {
        id: 'spliceqtl',
        label: 'spliceQTL',
        examples: [
          {
            label: 'Single result',
            items: [
              'gene_id = ENSG00000131236',
              'gene_name = CAP1',
              'method = spliceQTL, source = EBI',
              'biological_context = artery (tibial)'
            ]
          },
          {
            label: 'Group results',
            items: [
              'gene_id = ENSG00000131236',
              'gene_name = CAP1',
              'method = spliceQTL, source = EBI',
              'biological_context = artery (tibial)'
            ]
          }
        ]
      },
      {
        id: 'pqtl',
        label: 'pQTL',
        examples: [
          {
            label: 'Single result',
            items: [
              'variant_id = NC_000002.12:27508072:T:C',
              'spdi = NC_000002.12:27508072:T:C',
              'rsid = rs1260326',
              'ca_id = CA119886',
              'method = pQTL, source = UKB',
              'biological_context = blood plasma'
            ]
          },
          {
            label: 'Group results',
            items: [
              'variant_id = NC_000002.12:27508072:T:C',
              'spdi = NC_000002.12:27508072:T:C',
              'rsid = rs1260326',
              'ca_id = CA119886',
              'method = pQTL, source = UKB',
              'biological_context = blood plasma'
            ]
          }
        ]
      },
      {
        id: 'caqtl',
        label: 'caQTL',
        examples: [
          {
            label: 'Single result',
            items: [
              'region = chr1:40241650-40241654',
              'method = caQTL, source = AFGR',
              'biological_context = blood plasma'
            ]
          },
          {
            label: 'Group results',
            items: [
              'region = chr1:40241650-40241654',
              'method = caQTL, source = AFGR',
              'biological_context = blood plasma'
            ]
          }
        ]
      }
    ])
}
