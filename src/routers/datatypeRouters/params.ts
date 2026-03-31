import { z } from 'zod'
import { getCollectionEnumValuesOrThrow } from './schema'

export const variantsCommonQueryFormat = z.object({
  spdi: z.string().trim().optional(),
  hgvs: z.string().trim().optional(),
  rsid: z.string().trim().optional(),
  ca_id: z.string().trim().optional(),
  variant_id: z.string().trim().optional(),
  region: z.string().trim().optional()
})

export const genesCommonQueryFormat = z.object({
  gene_id: z.string().trim().optional(),
  hgnc_id: z.string().trim().optional(),
  gene_name: z.string().trim().optional(),
  alias: z.string().trim().optional()
})

const TRANSCRIPT_TYPES = getCollectionEnumValuesOrThrow('nodes', 'transcripts', 'transcript_type')

export const transcriptsCommonQueryFormat = z.object({
  transcript_id: z.string().trim().optional(),
  region: z.string().trim().optional(),
  transcript_type: z.enum(TRANSCRIPT_TYPES).optional()
})

export const proteinsCommonQueryFormat = z.object({
  protein_id: z.string().trim().optional(),
  protein_name: z.string().trim().optional(),
  uniprot_name: z.string().trim().optional(),
  uniprot_full_name: z.string().trim().optional(),
  dbxrefs: z.string().trim().optional()
})

const GENOMIC_ELEMENT_SOURCE_ANNOTATIONS = getCollectionEnumValuesOrThrow('nodes', 'genomic_elements', 'source_annotation')
export const genomicElementSourceAnnotation = z.enum(GENOMIC_ELEMENT_SOURCE_ANNOTATIONS)

const GENOMIC_ELEMENT_TYPES = getCollectionEnumValuesOrThrow('nodes', 'genomic_elements', 'type')
export const genomicElementType = z.enum(GENOMIC_ELEMENT_TYPES)

const GENOMIC_ELEMENT_SOURCES = getCollectionEnumValuesOrThrow('nodes', 'genomic_elements', 'source')
export const genomicElementSource = z.enum(GENOMIC_ELEMENT_SOURCES)

export const genomicElementCommonQueryFormat = z.object({
  region: z.string().trim().optional(),
  source_annotation: genomicElementSourceAnnotation.optional(),
  region_type: genomicElementType.optional(),
  source: genomicElementSource.optional()
})

export const diseasessCommonQueryFormat = z.object({
  disease_id: z.string().trim().optional(),
  disease_name: z.string().trim().optional()
})
const motifsSources = z.enum([
  'IGVF',
  'HOCOMOCOv11'
])
export const motifsCommonQueryFormat = z.object({
  tf_name: z.string().trim().optional(),
  source: motifsSources.optional()
})

export const commonBiosamplesQueryFormat = z.object({
  biosample_name: z.string().trim().optional()
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
