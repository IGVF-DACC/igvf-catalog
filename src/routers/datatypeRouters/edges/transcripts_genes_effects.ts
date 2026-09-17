import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonHumanEdgeParamsFormat } from '../params'
import { getSchema, getCollectionEnumValuesOrThrow } from '../schema'
import { transcriptFormat } from '../nodes/transcripts'
import { geneFormat } from '../nodes/genes'

const MAX_PAGE_SIZE = 500
const ENSEMBL_VERSION_RE = /\.\d+$/

const transcriptsGenesSchema = getSchema('data/schemas/edges/transcripts_genes.MORFTranscriptGene.json')
const transcriptsGenesCollectionName = 'transcripts_genes'
const transcriptSchema = getSchema('data/schemas/nodes/transcripts.Gencode.json')
const geneSchema = getSchema('data/schemas/nodes/genes.GencodeGene.json')
const METHODS = getCollectionEnumValuesOrThrow('edges', 'transcripts_genes', 'method')

const edgeQueryFormat = z.object({
  transcript_id: z.string().trim().optional(),
  gene_id: z.string().trim().optional(),
  morf_id: z.string().trim().optional(),
  files_fileset: z.string().optional(),
  method: z.enum(METHODS).optional(),
  significant: z.enum(['true']).optional()
})

const queryFormat = edgeQueryFormat.merge(commonHumanEdgeParamsFormat)

const outputFormat = z.array(z.object({
  name: z.string(),
  label: z.string(),
  method: z.string(),
  class: z.string(),
  source: z.string(),
  source_url: z.string(),
  files_filesets: z.string(),
  biological_context: z.string(),
  biosample_term: z.string(),
  treatments_term_ids: z.array(z.string()).nullish(),
  crispr_modality: z.string().nullish(),
  log2FC: z.number().nullish(),
  log2FC_se: z.number().nullish(),
  base_mean: z.number().nullish(),
  p_value: z.number().nullish(),
  p_value_adj: z.number().nullish(),
  neg_log10_pvalue: z.number().nullish(),
  neg_log10_pvalue_adj: z.number().nullish(),
  significant: z.boolean().nullish(),
  morf_id: z.string().nullish(),
  orf_gene: z.string().nullish(),
  ensembl_transcript_ids: z.array(z.string()).nullish(),
  refseq_transcript_ids: z.array(z.string()).nullish(),
  transcript: z.string().or(transcriptFormat.partial()),
  gene: z.string().or(geneFormat.partial())
}))

function stripEnsemblVersion (id: string): string {
  return id.replace(ENSEMBL_VERSION_RE, '')
}

function validateQuery (input: paramsFormatType, requiredKeys: string[]): void {
  const definedKeysCount = requiredKeys.filter(key => key in input && input[key] !== undefined).length
  if (definedKeysCount < 1) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: `At least one of these properties must be defined: ${requiredKeys.join(', ')}.`
    })
  }
}

function applyLimit (input: paramsFormatType): number {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  return limit
}

function buildCombinedFilter (...filters: string[]): string {
  return filters.filter((filter) => filter !== '').join(' AND ') || 'true'
}

function buildEdgeFilter (input: paramsFormatType): string {
  const transcriptId = input.transcript_id as string | undefined
  const geneId = input.gene_id as string | undefined
  delete input.transcript_id
  delete input.gene_id

  if (input.files_fileset !== undefined) {
    input.files_filesets = `files_filesets/${input.files_fileset as string}`
    delete input.files_fileset
  }
  if (input.significant === 'true') {
    input.significant = true
  } else {
    delete input.significant
  }

  const filters = getFilterStatements(transcriptsGenesSchema, input)
  delete input.files_filesets
  delete input.significant
  delete input.morf_id
  delete input.method

  const transcriptFilter = transcriptId !== undefined
    ? `record._from == 'transcripts/${stripEnsemblVersion(transcriptId)}'`
    : ''
  const geneFilter = geneId !== undefined
    ? `record._to == 'genes/${stripEnsemblVersion(geneId)}'`
    : ''
  return buildCombinedFilter(transcriptFilter, geneFilter, filters)
}

function buildQuery (params: {
  combinedFilter: string
  page: number
  limit: number
  verbose: boolean
}): string {
  const { combinedFilter, page, limit, verbose } = params
  return `
    LET edgeRecords = (
      FOR record IN ${transcriptsGenesCollectionName}
      FILTER ${combinedFilter}
      SORT record._key
      LIMIT ${page * limit}, ${limit}
      RETURN record
    )
    LET transcriptIDs = UNIQUE(edgeRecords[*]._from)
    LET geneIDs = UNIQUE(edgeRecords[*]._to)
    LET transcriptLookup = ${verbose
      ? `(FOR transcript IN ${transcriptSchema.db_collection_name as string} FILTER transcript._id IN transcriptIDs RETURN { [transcript._id]: {${getDBReturnStatements(transcriptSchema).replaceAll('record', 'transcript')}} })`
      : '[]'}
    LET geneLookup = ${verbose
      ? `(FOR gene IN ${geneSchema.db_collection_name as string} FILTER gene._id IN geneIDs RETURN { [gene._id]: {${getDBReturnStatements(geneSchema).replaceAll('record', 'gene')}} })`
      : '[]'}
    LET transcriptMap = MERGE(transcriptLookup)
    LET geneMap = MERGE(geneLookup)
    FOR record IN edgeRecords
      RETURN {
        'transcript': ${verbose ? 'transcriptMap[record._from]' : 'record._from'},
        'gene': ${verbose ? 'geneMap[record._to]' : 'record._to'},
        ${getDBReturnStatements(transcriptsGenesSchema)}
      }
  `
}

async function findTranscriptGeneEffects (input: paramsFormatType, requiredKeys: string[]): Promise<any[]> {
  validateQuery(input, requiredKeys)
  delete input.organism
  const limit = applyLimit(input)
  const page = input.page as number
  delete input.page
  const verbose = input.verbose === 'true'
  delete input.verbose

  const combinedFilter = buildEdgeFilter(input)
  const query = buildQuery({ combinedFilter, page, limit, verbose })
  return await (await db.query(query)).all()
}

const genesFromTranscripts = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/transcripts/genes/effects', description: descriptions.transcripts_genes_effects } })
  .input(queryFormat)
  .output(outputFormat)
  .query(async ({ input }) => await findTranscriptGeneEffects(input, ['transcript_id', 'gene_id', 'morf_id', 'files_fileset', 'method']))

const transcriptsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/transcripts/effects', description: descriptions.genes_transcripts_effects } })
  .input(queryFormat)
  .output(outputFormat)
  .query(async ({ input }) => await findTranscriptGeneEffects(input, ['gene_id', 'transcript_id', 'morf_id', 'files_fileset', 'method']))

export const transcriptsGenesEffectsRouters = {
  transcriptGeneEffectsFromTranscripts: genesFromTranscripts,
  transcriptGeneEffectsFromGenes: transcriptsFromGenes
}
