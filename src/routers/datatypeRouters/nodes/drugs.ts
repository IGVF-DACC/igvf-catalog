import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 100

const drugSchema = getSchema('data/schemas/nodes/drugs.PharmGKB.json')
const drugCollectionName = (drugSchema.accessible_via as Record<string, any>).name as string

export const drugsQueryFormat = z.object({
  drug_id: z.string().trim().optional(),
  name: z.string().trim().optional(),
  page: z.number().default(0)
})

export const drugFormat = z.object({
  _id: z.string(),
  name: z.string(),
  drug_ontology_terms: z.array(z.string()).optional(),
  source: z.string(),
  source_url: z.string()
})

async function drugSearch (input: paramsFormatType): Promise<any[]> {
  if (input.drug_id === undefined && input.name === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Either drug_id or name must be defined.'
    })
  }

  if (input.drug_id !== undefined) {
    const query = `
      FOR record IN ${drugCollectionName}
      FILTER record._key == '${decodeURIComponent(input.drug_id as string)}'
      RETURN { ${getDBReturnStatements(drugSchema)} }
    `
    const record = (await (await db.query(query)).all())[0]

    if (record === undefined) {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: `Record ${input.drug_id as string} not found.`
      })
    }

    return record
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const tokenQuery = `
    FOR record IN ${drugCollectionName}_text_en_no_stem_inverted_search_alias
      SEARCH TOKENS("${decodeURIComponent(input.name as string)}", "text_en_no_stem") ALL in record.name
      LIMIT ${input.page as number * limit}, ${limit}
      SORT BM25(record) DESC
      RETURN { ${getDBReturnStatements(drugSchema)} }
  `

  const textObjects = await (await db.query(tokenQuery)).all()
  if (textObjects.length === 0) {
    const fuzzyQuery = `
      FOR record IN ${drugCollectionName}_text_en_no_stem_inverted_search_alias
        SEARCH LEVENSHTEIN_MATCH(
          record.name,
          TOKENS("${decodeURIComponent(input.name as string)}", "text_en_no_stem")[0],
          1,    // max distance
          false // without transpositions
        )
        LIMIT ${input.page as number * limit}, ${limit}
        SORT BM25(record) DESC
        RETURN { ${getDBReturnStatements(drugSchema)} }
    `

    return await (await db.query(fuzzyQuery)).all()
  }

  return textObjects
}

const drugs = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/drugs', description: descriptions.drugs } })
  .input(drugsQueryFormat.merge(z.object({ limit: z.number().optional() })))
  .output(z.array(drugFormat).or(drugFormat))
  .query(async ({ input }) => await drugSearch(input))

export const drugsRouters = {
  drugs
}
