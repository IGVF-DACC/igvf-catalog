import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT, configType } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonNodesParamsFormat, transcriptsCommonQueryFormat } from '../params'

const MAX_PAGE_SIZE = 500

const schema = loadSchemaConfig()

export const transcriptFormat = z.object({
  _id: z.string(),
  transcript_type: z.string(),
  chr: z.string(),
  start: z.number(),
  end: z.number(),
  name: z.string(),
  gene_name: z.string(),
  source: z.string(),
  version: z.string(),
  source_url: z.string()
})

const humanTranscriptSchema = schema.transcript
const mouseTranscriptSchema = schema['transcript mouse']

async function findTranscriptByID (transcript_id: string, transcriptSchema: configType): Promise<any[]> {
  const query = `
    FOR record IN ${transcriptSchema.db_collection_name}
    FILTER record._key == '${decodeURIComponent(transcript_id)}'
    RETURN { ${getDBReturnStatements(transcriptSchema)} }
  `

  const record = (await (await db.query(query)).all())[0]

  if (record === undefined) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: `Record ${transcript_id as string} not found.`
    })
  }

  return record
}

async function findTranscripts (input: paramsFormatType, transcriptSchema: configType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filterBy = ''
  const filterSts = getFilterStatements(transcriptSchema, input)
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }

  const query = `
    FOR record IN ${transcriptSchema.db_collection_name}
    ${filterBy}
    SORT record.chr
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(transcriptSchema)} }
  `

  return await (await db.query(query)).all()
}

async function transcriptSearch (input: paramsFormatType): Promise<any[]> {
  let schema = humanTranscriptSchema

  if (input.organism === 'Mus musculus') {
    schema = mouseTranscriptSchema
  }

  delete input.organism

  if (input.transcript_id !== undefined) {
    return await findTranscriptByID(input.transcript_id as string, schema)
  }

  return await findTranscripts(preProcessRegionParam(input), schema)
}

const transcripts = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/transcripts', description: descriptions.transcripts } })
  .input(transcriptsCommonQueryFormat.merge(commonNodesParamsFormat))
  .output(z.array(transcriptFormat).or(transcriptFormat))
  .query(async ({ input }) => await transcriptSearch(input))

export const transcriptsRouters = {
  transcripts
}
