import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonNodesParamsFormat } from '../params'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 50

const SEARCH_ALIAS = 'proteins_text_en_no_stem_inverted_search_alias'

const proteinSchema = getSchema('data/schemas/nodes/proteins.GencodeProtein.json')
const proteinCollectionName = (proteinSchema.accessible_via as Record<string, any>).name as string

export const proteinsQueryFormat = z.object({
  protein_id: z.string().trim().optional(),
  name: z.string().trim().optional(),
  full_name: z.string().trim().optional(),
  dbxrefs: z.string().trim().optional()
}).merge(commonNodesParamsFormat)
const dbxrefFormat = z.object({ name: z.string(), id: z.string() })

export const proteinFormat = z.object({
  _id: z.string(),
  names: z.array(z.string()).nullish(),
  full_names: z.array(z.string()).nullish(),
  dbxrefs: z.array(dbxrefFormat).nullish(),
  organism: z.string(),
  source: z.string(),
  source_url: z.string()
})

export function proteinByIDQuery (proteinId: string): string {
  return `(
    FOR record IN ${proteinCollectionName}
    FILTER record._key == '${decodeURIComponent(proteinId)}' OR
            record.protein_id == '${decodeURIComponent(proteinId)}' OR
            '${decodeURIComponent(proteinId)}' IN record.uniprot_ids
    RETURN record._id
  )
  `
}

async function findProteinByID (proteinId: string): Promise<any[]> {
  const query = `
    FOR record IN ${proteinCollectionName}
    FILTER record._key == '${decodeURIComponent(proteinId)}' OR
            record.protein_id == '${decodeURIComponent(proteinId)}' OR
            '${decodeURIComponent(proteinId)}' IN record.uniprot_ids
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

  const filters = []
  if (input.name !== undefined) {
    const name = input.name as string
    delete input.name
    filters.push(`"${decodeURIComponent(name.toUpperCase())}" in record.names`)
  }

  if (input.full_name !== undefined) {
    const fullName = input.full_name as string
    delete input.full_name
    filters.push(`"${decodeURIComponent(fullName)}" in record.full_names`)
  }

  filters.push(getFilterStatements(proteinSchema, input))

  const filterBy = filters.length > 0 ? `FILTER ${filters.join(' AND ')}` : ''

  const query = `
    FOR record IN ${proteinCollectionName}
    ${filterBy}
    SORT record.chr
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(proteinSchema)} }
  `

  return await (await db.query(query)).all()
}

async function findProteinsByPrefixSearch (name: string, fullName: string, dbxrefs: string, filters: string, page: number, limit: number): Promise<any[]> {
  const fields: Record<string, string | undefined> = { names: name, full_names: fullName, 'dbxrefs.id': dbxrefs }
  const searchFilters = []
  for (const field in fields) {
    if (fields[field] !== undefined) {
      searchFilters.push(`STARTS_WITH(record.${field}, TOKENS("${decodeURIComponent(fields[field] as string)}", 'text_en_no_stem'))`)
    }
  }

  const query = `
    FOR record IN ${SEARCH_ALIAS}
    SEARCH ${searchFilters.join(' AND ')}
    ${filters}
    SORT BM25(record) DESC
    LIMIT ${page * limit}, ${limit}
    RETURN { ${getDBReturnStatements(proteinSchema)} }
  `

  return await (await db.query(query)).all()
}

async function findProteinsByFuzzySearch (name: string, fullName: string, dbxrefs: string, filters: string, page: number, limit: number): Promise<any[]> {
  const fields: Record<string, string | undefined> = { names: name, full_names: fullName, 'dbxrefs.id': dbxrefs }
  const searchFilters = []
  for (const field in fields) {
    if (fields[field] !== undefined) {
      searchFilters.push(`LEVENSHTEIN_MATCH(record.${field}, "${decodeURIComponent(fields[field] as string)}", 3, true)`)
    }
  }

  const query = `
    FOR record IN ${SEARCH_ALIAS}
    SEARCH ${searchFilters.join(' AND ')}
    ${filters}
    SORT BM25(record) DESC
    LIMIT ${page * limit}, ${limit}
    RETURN { ${getDBReturnStatements(proteinSchema)} }
  `

  return await (await db.query(query)).all()
}

async function findProteinsByTextSearch (input: paramsFormatType): Promise<any[]> {
  const name = input.name as string
  const fullName = input.full_name as string
  const dbxrefs = input.dbxrefs as string

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  // try exact match
  const exactObjects = await findProteins(input)
  if (exactObjects.length !== 0) {
    return exactObjects
  }

  delete input.name
  delete input.full_name
  delete input.dbxrefs

  let remainingFilters = getFilterStatements(proteinSchema, input)
  if (remainingFilters) {
    remainingFilters = `FILTER ${remainingFilters}`
  }

  // try prefix match
  const prefixObjects = await findProteinsByPrefixSearch(name, fullName, dbxrefs, remainingFilters, input.page as number, limit)
  if (prefixObjects.length !== 0) {
    return prefixObjects
  }

  // try fuzzy match
  return await findProteinsByFuzzySearch(name, fullName, dbxrefs, remainingFilters, input.page as number, limit)
}

async function proteinSearch (input: paramsFormatType): Promise<any[]> {
  if ('protein_id' in input) {
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
