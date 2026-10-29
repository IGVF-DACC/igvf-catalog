import { z } from 'zod'
import { TRPCError } from '@trpc/server'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { QUERY_LIMIT } from '../../../constants'
import { commonHumanEdgeParamsFormat } from '../params'
import { getDBReturnStatements, paramsFormatType } from '../_helpers'
import { getCollectionEnumValuesOrThrow, getSchema } from '../schema'
import { geneFormat } from '../nodes/genes'
import { genomicElementFormat } from '../nodes/genomic_elements'
import { transcriptFormat } from '../nodes/transcripts'
import { descriptions } from '../descriptions'

const schema = getSchema('data/schemas/edges/genes_transcripts_genomic_elements.OverexpressionATAC.json')
const geneSchema = getSchema('data/schemas/nodes/genes.GencodeGene.json')
const transcriptSchema = getSchema('data/schemas/nodes/transcripts.Gencode.json')
const elementSchema = getSchema('data/schemas/nodes/genomic_elements.OverexpressionATAC.json')
const methods = getCollectionEnumValuesOrThrow('edges', 'genes_transcripts_genomic_elements', 'method')
const identifier = z.string().trim().min(1).optional()
const inputFormat = z.object({
  gene_id: identifier,
  gene_name: identifier,
  transcript_id: identifier,
  genomic_element_id: identifier,
  accessible_region: identifier,
  files_fileset: identifier,
  method: z.enum(methods).optional(),
  perturbation: z.enum(getCollectionEnumValuesOrThrow('edges', 'genes_transcripts_genomic_elements', 'perturbation')).optional(),
  source: z.enum(getCollectionEnumValuesOrThrow('edges', 'genes_transcripts_genomic_elements', 'source')).optional(),
  significant: z.enum(['true', 'false']).optional(),
  biological_context: identifier,
  biosample_term: identifier,
  base_mean: identifier,
  log2FC: identifier,
  p_value: identifier,
  p_value_adj: identifier,
  neg_log10_pvalue: identifier,
  neg_log10_pvalue_adj: identifier,
  ...commonHumanEdgeParamsFormat.shape,
  page: z.number().int().nonnegative().default(0),
  limit: z.number().int().positive().optional()
})

const outputFormat = z.object({
  _id: z.string(),
  gene_transcript: z.string(),
  gene: z.string().or(geneFormat.partial()).nullable(),
  transcript: z.string().or(transcriptFormat.partial()).nullable(),
  accessible_genomic_element: z.string().or(genomicElementFormat.extend({ _id: z.string() })).nullable(),
  log2FC: z.number().nullable(),
  standard_error: z.number().nullish(),
  stat: z.number().nullish(),
  base_mean: z.number().nullish(),
  p_value: z.number().nullish(),
  p_value_adj: z.number().nullish(),
  neg_log10_pvalue: z.number().nullish(),
  neg_log10_pvalue_adj: z.number().nullish(),
  significant: z.boolean(),
  name: z.string(),
  inverse_name: z.string(),
  label: z.string(),
  class: z.string(),
  method: z.string(),
  perturbation: z.string(),
  source: z.string(),
  source_url: z.string(),
  files_filesets: z.string(),
  biological_context: z.string(),
  biosample_term: z.string(),
  treatments_term_ids: z.array(z.string()).nullish()
})

const handle = (collection: string, value: string): string => value.startsWith(`${collection}/`) ? value : `${collection}/${value}`

async function findEffects (input: paramsFormatType): Promise<any[]> {
  const required = ['gene_id', 'gene_name', 'transcript_id', 'genomic_element_id', 'accessible_region', 'files_fileset', 'method', 'perturbation']
  if (!required.some(key => input[key] !== undefined)) {
    throw new TRPCError({ code: 'BAD_REQUEST', message: `Define at least one of: ${required.join(', ')}.` })
  }
  const filters: string[] = []
  const bindVars: Record<string, unknown> = {
    limit: Math.min(Number(input.limit ?? QUERY_LIMIT), 500),
    offset: Number(input.page ?? 0) * Math.min(Number(input.limit ?? QUERY_LIMIT), 500)
  }
  const endpoints: Record<string, [string, string]> = {
    gene_id: ['relationship._from', 'genes/'],
    transcript_id: ['relationship._to', 'transcripts/'],
    genomic_element_id: ['record._to', 'genomic_elements/']
  }
  for (const [key, [field, prefix]] of Object.entries(endpoints)) {
    if (input[key] !== undefined) {
      filters.push(`${field} == @${key}`)
      const value = String(input[key]).replace(new RegExp(`^${prefix}`), '')
      bindVars[key] = prefix + (key === 'genomic_element_id' ? value : value.replace(/\.\d+(?=_PAR_Y$|$)/, ''))
    }
  }
  for (const [key, field] of Object.entries({ gene_name: 'DOCUMENT(relationship._from).name' })) {
    if (input[key] !== undefined) {
      filters.push(`${field} == @${key}`)
      bindVars[key] = input[key]
    }
  }
  for (const key of ['method', 'source', 'perturbation', 'biological_context']) {
    if (input[key] !== undefined) {
      filters.push(`record.${key} == @${key}`)
      bindVars[key] = input[key]
    }
  }
  if (input.files_fileset !== undefined) {
    filters.push('record.files_filesets == @files_fileset')
    bindVars.files_fileset = handle('files_filesets', String(input.files_fileset))
  }
  if (input.biosample_term !== undefined) {
    filters.push('record.biosample_term == @biosample_term')
    bindVars.biosample_term = handle('ontology_terms', String(input.biosample_term))
  }
  if (input.significant !== undefined) {
    filters.push('record.significant == @significant')
    bindVars.significant = input.significant === 'true'
  }
  let regionQuery = ''
  if (input.accessible_region !== undefined) {
    const match = /^(chr[\w]+):(\d+)-(\d+)$/.exec(String(input.accessible_region))
    if (match === null || !Number.isSafeInteger(Number(match[2])) || !Number.isSafeInteger(Number(match[3])) || Number(match[3]) <= Number(match[2])) {
      throw new TRPCError({ code: 'BAD_REQUEST', message: 'accessible_region must be a 0-based half-open chr:start-end interval with end > start.' })
    }
    bindVars.chrom = match[1]
    bindVars.start = Number(match[2])
    bindVars.end = Number(match[3])
    regionQuery = `LET targetIDs = (FOR peak IN genomic_elements
      FILTER peak.chr == @chrom AND peak.start < @end AND peak.end > @start
      RETURN peak._id)`
    filters.push('record._to IN targetIDs')
  }
  const operators: Record<string, string> = { gt: '>', gte: '>=', lt: '<', lte: '<=', eq: '==' }
  for (const key of ['base_mean', 'log2FC', 'p_value', 'p_value_adj', 'neg_log10_pvalue', 'neg_log10_pvalue_adj']) {
    if (input[key] === undefined) continue
    const parts = String(input[key]).split(':')
    const operator = parts.length === 1 ? '==' : operators[parts[0]]
    const raw = parts[parts.length - 1]
    if (parts.length > 2 || typeof operator !== 'string' || raw.trim() === '' || !Number.isFinite(Number(raw))) {
      throw new TRPCError({ code: 'BAD_REQUEST', message: `${key} must be a number or gt/gte/lt/lte/eq:number.` })
    }
    filters.push(`record.${key} != null AND record.${key} ${operator} @${key}`)
    bindVars[key] = Number(raw)
  }
  const verbose = input.verbose === 'true'
  const expand = (ref: string, nodeSchema: typeof geneSchema): string => `FIRST(FOR node IN [DOCUMENT(${ref})] FILTER node != null RETURN {${getDBReturnStatements(nodeSchema, false, '', [], false).replaceAll('record', 'node')}})`
  const query = `
    ${regionQuery}
    FOR record IN genes_transcripts_genomic_elements
    LET relationship = DOCUMENT(record._from)
    FILTER relationship != null
    FILTER ${filters.join(' AND ')}
    SORT record._key
    LIMIT @offset, @limit
    RETURN MERGE({${getDBReturnStatements(schema)}}, {
      _id: record._id,
      inverse_name: record.inverse_name,
      gene_transcript: record._from,
      gene: ${verbose ? expand('relationship._from', geneSchema) : 'relationship._from'},
      transcript: ${verbose ? expand('relationship._to', transcriptSchema) : 'relationship._to'},
      accessible_genomic_element: ${verbose ? expand('record._to', elementSchema) : 'record._to'}
    })`
  return await (await db.query(query, bindVars)).all()
}

export const genesTranscriptsGenomicElementsRouters = {
  genesTranscriptsGenomicElements: publicProcedure
    .meta({ openapi: { method: 'GET', path: '/genes/transcripts/genomic-elements', description: descriptions.genes_transcripts_genomic_elements } })
    .input(inputFormat)
    .output(z.array(outputFormat))
    .query(async ({ input }) => await findEffects(input))
}
