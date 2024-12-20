import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { paramsFormatType, getDBReturnStatements } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'

const schema = loadSchemaConfig()
const complexSchema = schema.complex

const complexQueryFormat = z.object({
  complex_id: z.string().trim().optional(),
  name: z.string().trim().optional(),
  description: z.string().trim().optional(),
  page: z.number().default(0)
})

export const complexFormat = z.object({
  _id: z.string(),
  name: z.string(),
  alias: z.array(z.string()).nullable(),
  molecules: z.array(z.string()).nullable(),
  evidence_code: z.string().nullable(),
  experimental_evidence: z.string().nullable(),
  description: z.string().nullable(),
  complex_assembly: z.string().or(z.array(z.string())).nullable(),
  complex_source: z.string().nullable(),
  reactome_xref: z.array(z.string()).nullable(),
  source: z.string(),
  source_url: z.string()
})

async function findComplexByID (id: string): Promise<any> {
  const query = `
    FOR record IN ${complexSchema.db_collection_name as string}
    FILTER record._key == '${decodeURIComponent(id)}'
    RETURN { ${getDBReturnStatements(complexSchema)} }
  `

  const cursor = await db.query(query)
  const record = (await cursor.all())[0]

  if (record === undefined) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: `Complex ${id} not found.`
    })
  }

  return record
}

export async function complexSearch (input: paramsFormatType): Promise<any[]> {
  if (input.complex_id !== undefined) {
    return await findComplexByID(input.complex_id as string)
  }

  const fuzzyFilters = []
  if (input.name !== undefined) {
    fuzzyFilters.push(`TOKENS("${decodeURIComponent(input.name as string)}", "text_en_no_stem") ALL in record.name`)
  }
  if (input.description !== undefined) {
    fuzzyFilters.push(`TOKENS("${decodeURIComponent(input.description as string)}", "text_en_no_stem") ALL in record.description`)
  }

  if (fuzzyFilters.length > 0) {
    const searchViewName = `${complexSchema.db_collection_name as string}_text_en_no_stem_inverted_search_alias`

    const query = `
      FOR record IN ${searchViewName}
      SEARCH ${fuzzyFilters.join(' AND ')}
      LIMIT ${input.page as number * QUERY_LIMIT}, ${QUERY_LIMIT}
      SORT BM25(record) DESC
      RETURN { ${getDBReturnStatements(complexSchema)} }
    `

    return await (await db.query(query)).all()
  }

  throw new TRPCError({
    code: 'BAD_REQUEST',
    message: 'At least one parameter must be defined.'
  })
}

export const complexes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/complexes', description: descriptions.complex } })
  .input(complexQueryFormat)
  .output(z.array(complexFormat).or(complexFormat))
  .query(async ({ input }) => await complexSearch(input))

export const complexesRouters = {
  complexes
}
