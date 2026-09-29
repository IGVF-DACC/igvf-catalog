import { z } from 'zod'
import { TRPCError } from '@trpc/server'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { QUERY_LIMIT } from '../../../constants'
import { commonHumanEdgeParamsFormat } from '../params'
import { getDBReturnStatements, paramsFormatType } from '../_helpers'
import { getCollectionEnumValuesOrThrow, getSchema } from '../schema'
import { geneFormat } from '../nodes/genes'
import { transcriptFormat } from '../nodes/transcripts'
import { descriptions } from '../descriptions'

const schema = getSchema('data/schemas/edges/genes_transcripts_genes.MORFGeneTranscriptGene.json')
const geneSchema = getSchema('data/schemas/nodes/genes.GencodeGene.json')
const transcriptSchema = getSchema('data/schemas/nodes/transcripts.Gencode.json')
const methods = getCollectionEnumValuesOrThrow('edges', 'genes_transcripts_genes', 'method')
const identifier = z.string().trim().min(1).optional()
const inputFormat = z.object({
  gene_id: identifier,
  gene_name: identifier,
  transcript_id: identifier,
  associated_gene_id: identifier,
  associated_gene_name: identifier,
  morf_id: identifier,
  files_fileset: identifier,
  method: z.enum(methods).optional(),
  significant: z.enum(['true']).optional(),
  biological_context: identifier,
  biosample_term: identifier,
  log2FC: identifier,
  p_value: identifier,
  p_value_adj: identifier,
  neg_log10_pvalue: identifier,
  neg_log10_pvalue_adj: identifier
}).merge(commonHumanEdgeParamsFormat)

const outputFormat = z.object({
  _id: z.string(),
  gene_transcript: z.string(),
  gene: z.string().or(geneFormat.partial()).nullable(),
  transcript: z.string().or(transcriptFormat.partial()).nullable(),
  associated_gene: z.string().or(geneFormat.partial()).nullable(),
  morf_id: z.string(),
  transcript_mapping_method: z.string(),
  log2FC: z.number(),
  standard_error: z.number().nullish(),
  base_mean: z.number().nullish(),
  p_value: z.number().nullish(),
  p_value_adj: z.number().nullish(),
  neg_log10_pvalue: z.number().nullish(),
  neg_log10_pvalue_adj: z.number().nullish(),
  significant: z.boolean(),
  name: z.string(),
  label: z.string(),
  class: z.string(),
  method: z.string(),
  source: z.string(),
  source_url: z.string(),
  files_filesets: z.string(),
  biological_context: z.string(),
  biosample_term: z.string(),
  treatments_term_ids: z.array(z.string()).nullish()
})

async function findEffects (input: paramsFormatType): Promise<any[]> {
  const required = ['gene_id', 'gene_name', 'transcript_id', 'associated_gene_id', 'associated_gene_name', 'morf_id', 'files_fileset', 'method']
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
    associated_gene_id: ['record._to', 'genes/']
  }
  for (const [key, [field, prefix]] of Object.entries(endpoints)) {
    if (input[key] !== undefined) {
      filters.push(`${field} == @${key}`)
      bindVars[key] = prefix + String(input[key]).replace(/\.\d+(?=_PAR_Y$|$)/, '')
    }
  }
  for (const [key, field] of Object.entries({ gene_name: 'DOCUMENT(relationship._from).name', associated_gene_name: 'DOCUMENT(record._to).name' })) {
    if (input[key] !== undefined) {
      filters.push(`${field} == @${key}`)
      bindVars[key] = input[key]
    }
  }
  for (const key of ['morf_id', 'method', 'biological_context', 'biosample_term']) {
    if (input[key] !== undefined) {
      filters.push(`record.${key} == @${key}`)
      bindVars[key] = input[key]
    }
  }
  if (input.files_fileset !== undefined) {
    filters.push('record.files_filesets == @files_fileset')
    bindVars.files_fileset = `files_filesets/${String(input.files_fileset)}`
  }
  if (input.significant === 'true') filters.push('record.significant == true')
  const operators: Record<string, string> = { gt: '>', gte: '>=', lt: '<', lte: '<=', eq: '==' }
  for (const key of ['log2FC', 'p_value', 'p_value_adj', 'neg_log10_pvalue', 'neg_log10_pvalue_adj']) {
    if (input[key] === undefined) continue
    const parts = String(input[key]).split(':')
    const operator = parts.length === 1 ? '==' : operators[parts[0]]
    const raw = parts[parts.length - 1]
    if (parts.length > 2 || operator === undefined || raw.trim() === '' || !Number.isFinite(Number(raw))) {
      throw new TRPCError({ code: 'BAD_REQUEST', message: `${key} must be a number or gt/gte/lt/lte/eq:number.` })
    }
    filters.push(`record.${key} != null AND record.${key} ${operator} @${key}`)
    bindVars[key] = Number(raw)
  }
  const verbose = input.verbose === 'true'
  const expand = (ref: string, nodeSchema: typeof geneSchema): string => `FIRST(FOR node IN [DOCUMENT(${ref})] FILTER node != null RETURN {${getDBReturnStatements(nodeSchema).replaceAll('record', 'node')}})`
  const query = `
    FOR record IN genes_transcripts_genes
    LET relationship = DOCUMENT(record._from)
    FILTER relationship != null
    FILTER ${filters.join(' AND ')}
    SORT record._key
    LIMIT @offset, @limit
    RETURN MERGE({${getDBReturnStatements(schema)}}, {
      _id: record._id,
      gene_transcript: record._from,
      gene: ${verbose ? expand('relationship._from', geneSchema) : 'relationship._from'},
      transcript: ${verbose ? expand('relationship._to', transcriptSchema) : 'relationship._to'},
      associated_gene: ${verbose ? expand('record._to', geneSchema) : 'record._to'}
    })`
  return await (await db.query(query, bindVars)).all()
}

export const genesTranscriptsGenesRouters = {
  genesTranscriptsGenes: publicProcedure
    .meta({ openapi: { method: 'GET', path: '/genes/transcripts/genes', description: descriptions.genes_transcripts_genes } })
    .input(inputFormat)
    .output(z.array(outputFormat))
    .query(async ({ input }) => await findEffects(input))
}
