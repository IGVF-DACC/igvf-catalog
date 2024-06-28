import { z } from 'zod'
import { geneTypes } from './nodes/genes'
import { biochemicalActivity, regulatoryRegionSource, regulatoryRegionType } from './nodes/regulatory_regions'

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

export const variantsHumanCommonQueryFormat = z.object({
  spdi: z.string().trim().optional(),
  hgvs: z.string().trim().optional(),
  rsid: z.string().trim().optional(),
  variant_id: z.string().trim().optional(),
  chr: z.string().trim().optional(),
  position: z.string().trim().optional()
})

export const genesCommonQueryFormat = z.object({
  gene_id: z.string().trim().optional(),
  hgnc: z.string().trim().optional(),
  gene_name: z.string().trim().optional(),
  region: z.string().trim().optional(),
  alias: z.string().trim().optional(),
  gene_type: geneTypes.optional()
})

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
const motifsSources = z.enum(['HOCOMOCOv11'])
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
