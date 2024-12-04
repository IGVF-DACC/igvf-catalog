import { z } from 'zod'

export const variantsCommonQueryFormat = z.object({
  spdi: z.string().trim().optional(),
  hgvs: z.string().trim().optional(),
  rsid: z.string().trim().optional(),
  variant_id: z.string().trim().optional(),
  chr: z.string().trim().optional(),
  position: z.string().trim().optional()
})

export const geneTypes = z.enum([
  'IG_V_pseudogene',
  'lncRNA',
  'miRNA',
  'misc_RNA',
  'processed_pseudogene',
  'protein_coding',
  'pseudogene',
  'rRNA',
  'rRNA_pseudogene',
  'scaRNA',
  'snoRNA',
  'snRNA',
  'TEC',
  'transcribed_processed_pseudogene',
  'transcribed_unitary_pseudogene',
  'transcribed_unprocessed_pseudogene',
  'unitary_pseudogene',
  'unprocessed_pseudogene',
  'ribozyme',
  'translated_unprocessed_pseudogene',
  'sRNA',
  'IG_C_gene',
  'IG_C_pseudogene',
  'IG_D_gene',
  'IG_J_gene',
  'IG_J_pseudogene',
  'IG_pseudogene',
  'IG_V_gene',
  'TR_C_gene',
  'TR_D_gene',
  'TR_J_gene',
  'TR_J_pseudogene',
  'TR_V_gene',
  'TR_V_pseudogene',
  'translated_processed_pseudogene',
  'scRNA',
  'artifact',
  'vault_RNA',
  'Mt_rRNA',
  'Mt_tRNA'
])

export const genesCommonQueryFormat = z.object({
  gene_id: z.string().trim().optional(),
  hgnc: z.string().trim().optional(),
  gene_name: z.string().trim().optional(),
  alias: z.string().trim().optional()
})

export const transcriptTypes = z.enum([
  'rRNA_pseudogene',
  'misc_RNA',
  'protein_coding',
  'protein_coding_CDS_not_defined',
  'unprocessed_pseudogene',
  'retained_intron',
  'nonsense_mediated_decay',
  'lncRNA',
  'processed_pseudogene',
  'transcribed_processed_pseudogene',
  'processed_transcript',
  'protein_coding_LoF',
  'transcribed_unprocessed_pseudogene',
  'transcribed_unitary_pseudogene',
  'non_stop_decay',
  'snoRNA',
  'TEC',
  'scaRNA',
  'miRNA',
  'snRNA',
  'pseudogene',
  'unitary_pseudogene',
  'IG_V_pseudogene',
  'rRNA',
  'ribozyme',
  'translated_unprocessed_pseudogene',
  'sRNA',
  'IG_pseudogene',
  'TR_V_gene',
  'IG_C_gene',
  'IG_D_gene',
  'IG_C_pseudogene',
  'IG_J_gene',
  'IG_J_pseudogene',
  'IG_V_gene',
  'TR_C_gene',
  'TR_J_gene',
  'TR_J_pseudogene',
  'TR_V_pseudogene',
  'TR_D_gene',
  'translated_processed_pseudogene',
  'scRNA',
  'artifact',
  'vault_RNA',
  'Mt_rRNA',
  'Mt_tRNA'
])

export const transcriptsCommonQueryFormat = z.object({
  transcript_id: z.string().trim().optional(),
  region: z.string().trim().optional(),
  transcript_type: transcriptTypes.optional()
})

export const proteinsCommonQueryFormat = z.object({
  protein_id: z.string().trim().optional(),
  protein_name: z.string().trim().optional(),
  full_name: z.string().trim().optional(),
  dbxrefs: z.string().trim().optional()
})
export const biochemicalActivity = z.enum([
  'CA',
  'CA-CTCF',
  'CA-H3K4me3',
  'CA-TF',
  'dELS',
  'ENH',
  'pELS',
  'PLS',
  'PRO',
  'TF'
])

export const regulatoryRegionType = z.enum([
  'candidate_cis_regulatory_element',
  'accessible dna elements',
  'MPRA_tested_regulatory_element',
  'CRISPR_tested_element',
  'enhancer',
  'accessible dna elements (mouse)'
])

export const regulatoryRegionSource = z.enum([
  'AFGR',
  'ENCODE-E2G',
  'ENCODE-E2G-CRISPR',
  'ENCODE_EpiRaction',
  'ENCODE_MPRA',
  'ENCODE_SCREEN (ccREs)',
  'FUNCODE',
  'PMID:34017130',
  'PMID:34038741'
])
export const regulatoryRegionsCommonQueryFormat = z.object({
  region: z.string().trim().optional(),
  biochemical_activity: biochemicalActivity.optional(),
  region_type: regulatoryRegionType.optional(),
  source: regulatoryRegionSource.optional()
})

export const diseasessCommonQueryFormat = z.object({
  disease_id: z.string().trim().optional(),
  disease_name: z.string().trim().optional()
})
const motifsSources = z.enum(['HOCOMOCOv11', 'SEMpl'])
export const motifsCommonQueryFormat = z.object({
  tf_name: z.string().trim().optional(),
  source: motifsSources.optional()
})

export const commonBiosamplesQueryFormat = z.object({
  biosample_id: z.string().trim().optional(),
  biosample_name: z.string().trim().optional(),
  biosample_synonyms: z.string().trim().optional()
})

export const commonComplexQueryFormat = z.object({
  complex_id: z.string().trim().optional(),
  complex_name: z.string().trim().optional(),
  description: z.string().trim().optional()
})

export const commonDrugsQueryFormat = z.object({
  drug_id: z.string().trim().optional(),
  drug_name: z.string().trim().optional()
})

export const commonPathwayQueryFormat = z.object({
  pathway_id: z.string().trim().optional(),
  pathway_name: z.string().trim().optional(),
  name_aliases: z.string().trim().optional(),
  disease_ontology_terms: z.string().trim().optional(),
  go_biological_process: z.string().trim().optional()
})

export const commonHumanEdgeParamsFormat = z.object({
  organism: z.enum(['Homo sapiens']).default('Homo sapiens'),
  verbose: z.enum(['true', 'false']).default('false'),
  page: z.number().default(0),
  limit: z.number().optional()
})

export const commonEdgeParamsFormat = z.object({
  organism: z.enum(['Mus musculus', 'Homo sapiens']).default('Homo sapiens'),
  verbose: z.enum(['true', 'false']).default('false'),
  page: z.number().default(0),
  limit: z.number().optional()
})

export const commonHumanNodesParamsFormat = z.object({
  organism: z.enum(['Homo sapiens']).default('Homo sapiens'),
  page: z.number().default(0),
  limit: z.number().optional()
})

export const commonNodesParamsFormat = z.object({
  organism: z.enum(['Mus musculus', 'Homo sapiens']).default('Homo sapiens'),
  page: z.number().default(0),
  limit: z.number().optional()
})
