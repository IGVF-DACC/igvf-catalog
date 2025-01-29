import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonNodesParamsFormat } from '../params'

const MAX_PAGE_SIZE = 50

const schema = loadSchemaConfig()

export const proteinsQueryFormat = z.object({
  protein_id: z.string().trim().optional(),
  name: z.string().trim().optional(),
  full_name: z.string().trim().optional(),
  dbxrefs: z.string().trim().optional()
}).merge(commonNodesParamsFormat)
const dbxrefFormat = z.object({ name: z.string(), id: z.string() })

export const proteinFormat = z.object({
  _id: z.string(),
  name: z.string(),
  full_name: z.string().optional(),
  dbxrefs: z.array(dbxrefFormat).optional(),
  source: z.string(),
  source_url: z.string()
})

const proteinSchema = schema.protein

async function findProteinByID (proteinId: string): Promise<any[]> {
  const query = `
    FOR record IN ${proteinSchema.db_collection_name as string}
    FILTER record._key == '${decodeURIComponent(proteinId)}'
    RETURN { ${getDBReturnStatements(proteinSchema)} }
  `

  const record = (await (await db.query(query)).all())[0]

  if (record === undefined) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: `Record ${proteinId} not found.`
    })
  }

  return record
}

async function findProteins (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filterBy = ''
  const filterSts = getFilterStatements(proteinSchema, input)
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }

  const query = `
    FOR record IN ${proteinSchema.db_collection_name as string}
    ${filterBy}
    SORT record.chr
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(proteinSchema)} }
  `
  return await (await db.query(query)).all()
}

async function findProteinsByTextSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const exactObjects = await findProteins(input)
  if (exactObjects.length !== 0) {
    return exactObjects
  }

  const name = input.name as string
  delete input.name
  const fullName = input.full_name as string
  delete input.full_name
  const dbxrefs = input.dbxrefs as string
  delete input.dbxrefs

  let remainingFilters = getFilterStatements(proteinSchema, input)
  if (remainingFilters) {
    remainingFilters = `FILTER ${remainingFilters}`
  }

  const query = (searchFilters: string[]): string => {
    return `
      FOR record IN ${proteinSchema.db_collection_name as string}_text_delimiter_inverted_search_alias
        SEARCH ${searchFilters.join(' AND ')}
        ${remainingFilters}
        LIMIT ${input.page as number * limit}, ${limit}
        SORT BM25(record) DESC
        RETURN { ${getDBReturnStatements(proteinSchema)} }
    `
  }

  let searchFilters = []

  const analyzers = ['text_en_no_stem', 'text_delimiter']
  for (let index = 0; index < analyzers.length; index++) {
    const analyzer = analyzers[index]

    searchFilters = []

    if (name !== undefined) {
      searchFilters.push(`TOKENS("${decodeURIComponent(name)}", "${analyzer}") ALL in record.name`)
    }
    if (fullName !== undefined) {
      searchFilters.push(`TOKENS("${decodeURIComponent(fullName)}", "${analyzer}") ALL in record.full_name`)
    }
    if (dbxrefs !== undefined) {
      searchFilters.push(`TOKENS("${decodeURIComponent(dbxrefs)}", "${analyzer}") ALL in record.dbxrefs.id`)
    }

    const tokenObjects = await (await db.query(query(searchFilters))).all()
    if (tokenObjects.length !== 0) {
      return tokenObjects
    }
  }

  searchFilters = []
  if (name !== undefined) {
    searchFilters.push(`LEVENSHTEIN_MATCH(record.name, TOKENS("${decodeURIComponent(name)}", "text_en_no_stem")[0], 1, false)`)
  }
  if (fullName !== undefined) {
    searchFilters.push(`LEVENSHTEIN_MATCH(record.full_name, TOKENS("${decodeURIComponent(fullName)}", "text_en_no_stem")[0], 1, false)`)
  }
  if (dbxrefs !== undefined) {
    searchFilters.push(`LEVENSHTEIN_MATCH(record.dbxrefs.id, TOKENS("${decodeURIComponent(dbxrefs)}", "text_en_no_stem")[0], 1, false)`)
  }

  return await (await db.query(query(searchFilters))).all()
}

async function proteinSearch (input: paramsFormatType): Promise<any[]> {
  if (input.protein_id !== undefined) {
    return await findProteinByID(input.protein_id as string)
  }

  if ('name' in input || 'full_name' in input || 'dbxrefs' in input) {
    return await findProteinsByTextSearch(input)
  }

  return await findProteins(input)
}

const proteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins', description: descriptions.proteins } })
  .input(proteinsQueryFormat)
  .output(z.array(proteinFormat).or(proteinFormat))
  .query(async ({ input }) => await proteinSearch(input))

export const proteinsRouters = {
  proteins
}
