import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { transcriptFormat } from '../nodes/transcripts'
import { proteinByIDQuery, proteinFormat } from '../nodes/proteins'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonEdgeParamsFormat, proteinsCommonQueryFormat, transcriptsCommonQueryFormat } from '../params'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 100

const proteinTranscriptFormat = z.object({
  source: z.string().optional(),
  source_url: z.string().optional(),
  protein: z.string().or(z.array(proteinFormat)).optional(),
  transcript: z.string().or(transcriptFormat).optional(),
  name: z.string()
})

const transcriptToProteinSchema = getSchema('data/schemas/edges/transcripts_proteins.GencodeProtein.json')
const transcriptToProteinCollectionName = transcriptToProteinSchema.db_collection_name as string
const transcriptSchemaHuman = getSchema('data/schemas/nodes/transcripts.Gencode.json')
const transcriptSchemaMouse = getSchema('data/schemas/nodes/mm_transcripts.Gencode.json')
const proteinSchema = getSchema('data/schemas/nodes/proteins.GencodeProtein.json')
const proteinCollectionName = proteinSchema.db_collection_name as string

async function findProteinsFromTranscriptSearch (input: paramsFormatType): Promise<any[]> {
  let transcriptSchema = transcriptSchemaHuman
  if (input.organism === 'Mus musculus') {
    transcriptSchema = transcriptSchemaMouse
  }
  const transcriptCollectionName = transcriptSchema.db_collection_name as string
  if (input.transcript_id === undefined && input.region === undefined && input.transcript_type === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one transcript parameter must be defined.'
    })
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const proteinVerboseQuery = `
    FOR otherRecord IN ${proteinCollectionName}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(proteinSchema).replaceAll('record', 'otherRecord')}}
  `

  let query
  if (input.transcript_id !== undefined) {
    query = `
      LET transcriptIds = (
        FOR record IN ${transcriptCollectionName}
        FILTER record._key == '${input.transcript_id as string}'
        RETURN record._id
      )

      FOR record IN ${transcriptToProteinCollectionName}
      FILTER record._from in transcriptIds
      SORT record.chr
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'transcript': record._from,
        'protein': ${input.verbose === 'true' ? `(${proteinVerboseQuery})` : 'record._to'},
        ${getDBReturnStatements(transcriptToProteinSchema)},
        'name': record.name
      }
    `
  } else {
    query = `
      LET sources = (
        FOR record in ${transcriptCollectionName}
        FILTER ${getFilterStatements(transcriptSchema, preProcessRegionParam(input))}
        RETURN record._id
      )

      FOR record IN ${transcriptToProteinCollectionName}
        FILTER record._from IN sources
        SORT record.chr
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN {
          'transcript': record._from,
          'protein': ${input.verbose === 'true' ? `(${proteinVerboseQuery})` : 'record._to'},
          ${getDBReturnStatements(transcriptToProteinSchema)},
          'name': record.name
        }
    `
  }
  return await (await db.query(query)).all()
}

export async function findTranscriptsFromProteinSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const transcriptVerboseQuery = `
    (FOR otherRecord IN ${transcriptSchemaHuman.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(transcriptSchemaHuman).replaceAll('record', 'otherRecord')}})[0]
    ||
    (FOR otherRecord IN ${transcriptSchemaMouse.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(transcriptSchemaHuman).replaceAll('record', 'otherRecord')}})[0]
  `

  let query
  if (input.protein_id !== undefined) {
    query = `
      LET proteinIds = ${proteinByIDQuery(input.protein_id as string)}
      FOR record IN ${transcriptToProteinCollectionName}
      FILTER record._to in proteinIds
      SORT record.chr
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'protein': record._to,
        'transcript': ${input.verbose === 'true' ? `(${transcriptVerboseQuery})` : 'record._from'},
        ${getDBReturnStatements(transcriptToProteinSchema)},
        'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
      }
    `
  } else {
    input.names = input.protein_name
    input.full_names = input.full_name
    delete input.protein_name
    delete input.full_name

    query = `
      LET targets = (
        FOR record IN ${proteinCollectionName}
        FILTER ${getFilterStatements(proteinSchema, input)}
        RETURN record._id
      )

      FOR record IN ${transcriptToProteinCollectionName}
        FILTER record._to IN targets
        SORT record.chr
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN {
          'protein': record._to,
          'transcript': ${input.verbose === 'true' ? `(${transcriptVerboseQuery})` : 'record._from'},
          ${getDBReturnStatements(transcriptToProteinSchema)},
          'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
        }
    `
  }

  return await (await db.query(query)).all()
}

const proteinsFromTranscripts = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/transcripts/proteins', description: descriptions.transcripts_proteins } })
  .input(transcriptsCommonQueryFormat.merge(commonEdgeParamsFormat))
  .output(z.array(proteinTranscriptFormat))
  .query(async ({ input }) => await findProteinsFromTranscriptSearch(input))

const transcriptsFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/transcripts', description: descriptions.proteins_transcripts } })
  .input(proteinsCommonQueryFormat.merge(commonEdgeParamsFormat))
  .output(z.array(proteinTranscriptFormat))
  .query(async ({ input }) => await findTranscriptsFromProteinSearch(input))

export const transcriptsProteinsRouters = {
  proteinsFromTranscripts,
  transcriptsFromProteins
}
