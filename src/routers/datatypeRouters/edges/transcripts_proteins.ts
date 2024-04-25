import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { transcriptFormat, transcriptsQueryFormat } from '../nodes/transcripts'
import { proteinFormat, proteinsQueryFormat } from '../nodes/proteins'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'

const MAX_PAGE_SIZE = 100

const proteinTranscriptFormat = z.object({
  source: z.string().optional(),
  source_url: z.string().optional(),
  protein: z.string().or(z.array(proteinFormat)).optional(),
  transcript: z.string().or(transcriptFormat).optional()
})

const schema = loadSchemaConfig()

const transcriptToProteinSchema = schema['translates to']
const transcriptSchema = schema.transcript
const proteinSchema = schema.protein

async function findProteinsFromTranscriptSearch (input: paramsFormatType): Promise<any[]> {
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
    FOR otherRecord IN ${proteinSchema.db_collection_name}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(proteinSchema).replaceAll('record', 'otherRecord')}}
  `

  let query
  if (input.transcript_id !== undefined) {
    query = `
      FOR record IN ${transcriptToProteinSchema.db_collection_name}
      FILTER record._from == 'transcripts/${decodeURIComponent(input.transcript_id as string)}'
      SORT record.chr
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'protein': ${input.verbose === 'true' ? `(${proteinVerboseQuery})` : 'record._to'},
        ${getDBReturnStatements(transcriptToProteinSchema)}
      }
    `
  } else {
    query = `
      LET sources = (
        FOR record in ${transcriptSchema.db_collection_name}
        FILTER ${getFilterStatements(transcriptSchema, preProcessRegionParam(input))}
        RETURN record._id
      )

      FOR record IN ${transcriptToProteinSchema.db_collection_name}
        FILTER record._from IN sources
        SORT record.chr
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN {
          'protein': ${input.verbose === 'true' ? `(${proteinVerboseQuery})` : 'record._to'},
          ${getDBReturnStatements(transcriptToProteinSchema)}
        }
    `
  }

  return await (await db.query(query)).all()
}

async function findTranscriptsFromProteinSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const transcriptVerboseQuery = `
    FOR otherRecord IN ${transcriptSchema.db_collection_name}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(transcriptSchema).replaceAll('record', 'otherRecord')}}
  `

  let query
  if (input.protein_id !== undefined) {
    query = `
      FOR record IN ${transcriptToProteinSchema.db_collection_name}
      FILTER record._to == 'proteins/${decodeURIComponent(input.protein_id as string)}'
      SORT record.chr
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'transcript': ${input.verbose === 'true' ? `(${transcriptVerboseQuery})[0]` : 'record._from'},
        ${getDBReturnStatements(transcriptToProteinSchema)}
      }
    `
  } else {
    input.name = input.protein_name
    delete input.protein_name

    query = `
      LET targets = (
        FOR record IN ${proteinSchema.db_collection_name}
        FILTER ${getFilterStatements(proteinSchema, input)}
        RETURN record._id
      )

      FOR record IN ${transcriptToProteinSchema.db_collection_name}
        FILTER record._to IN targets
        SORT record.chr
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN {
          'transcript': ${input.verbose === 'true' ? `(${transcriptVerboseQuery})[0]` : 'record._from'},
          ${getDBReturnStatements(transcriptToProteinSchema)}
        }
    `
  }

  return await (await db.query(query)).all()
}

const proteinQuery = z.object({ protein_name: z.string().optional() }).merge(proteinsQueryFormat.omit({ organism: true, name: true }))

const proteinsFromTranscripts = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/transcripts/proteins', description: descriptions.transcripts_proteins } })
  .input(transcriptsQueryFormat.omit({ organism: true }).merge(z.object({ limit: z.number().optional(), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(proteinTranscriptFormat))
  .query(async ({ input }) => await findProteinsFromTranscriptSearch(input))

const transcriptsFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/transcripts', description: descriptions.proteins_transcripts } })
  .input(proteinQuery.merge(z.object({ limit: z.number().optional(), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(proteinTranscriptFormat))
  .query(async ({ input }) => await findTranscriptsFromProteinSearch(input))

export const transcriptsProteinsRouters = {
  proteinsFromTranscripts,
  transcriptsFromProteins
}
