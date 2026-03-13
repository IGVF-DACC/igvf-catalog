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
const proteinCollectionName = proteinSchema.db_collection_name as string

export const proteinsQueryFormat = z.object({
  protein_id: z.string().trim().optional(),
  name: z.string().trim().optional(),
  uniprot_name: z.string().trim().optional(),
  uniprot_full_name: z.string().trim().optional(),
  dbxrefs: z.string().trim().optional()
}).merge(commonNodesParamsFormat)
const dbxrefFormat = z.object({ name: z.string(), id: z.string() })

export const proteinFormat = z.object({
  _id: z.string(),
  name: z.string().nullish(),
  uniprot_names: z.array(z.string()).nullish(),
  uniprot_full_names: z.array(z.string()).nullish(),
  dbxrefs: z.array(dbxrefFormat).nullish(),
  MANE_Select: z.boolean().nullish(),
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
    const proteinName = input.name as string
    delete input.name
    filters.push(`"${decodeURIComponent(proteinName.toUpperCase())}" == record.name`)
  }
  if (input.uniprot_name !== undefined) {
    const uniprotName = input.uniprot_name as string
    delete input.uniprot_name
    filters.push(`"${decodeURIComponent(uniprotName.toUpperCase())}" in record.uniprot_names`)
  }

  if (input.uniprot_full_name !== undefined) {
    const fullName = input.uniprot_full_name as string
    delete input.uniprot_full_name
    filters.push(`"${decodeURIComponent(fullName)}" in record.uniprot_full_names`)
  }

  const additionalFilters = getFilterStatements(proteinSchema, input)
  if (additionalFilters !== '') {
    filters.push(additionalFilters)
  }

  const filterBy = filters.length > 0 ? `FILTER ${filters.join(' AND ')}` : ''

  const query = `
    FOR record IN ${proteinCollectionName}
    ${filterBy}
    SORT record.chr
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(proteinSchema)} }
  `
  const results = await (await db.query(query)).all()
  return results
}

async function findProteinsByPrefixSearch (uniprotName: string, uniprotFullName: string, dbxrefs: string, filters: string, page: number, limit: number): Promise<any[]> {
  const fields: Record<string, string | undefined> = { uniprot_names: uniprotName, uniprot_full_names: uniprotFullName, 'dbxrefs.id': dbxrefs }
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

async function findProteinsByFuzzySearch (uniprotName: string, uniprotFullName: string, dbxrefs: string, filters: string, page: number, limit: number): Promise<any[]> {
  const fields: Record<string, string | undefined> = { uniprot_names: uniprotName, uniprot_full_names: uniprotFullName, 'dbxrefs.id': dbxrefs }
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
  const uniprotName = input.uniprot_name as string
  const fullName = input.uniprot_full_name as string
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

  delete input.uniprot_name
  delete input.uniprot_full_name
  delete input.dbxrefs

  let remainingFilters = getFilterStatements(proteinSchema, input)
  if (remainingFilters) {
    remainingFilters = `FILTER ${remainingFilters}`
  }

  // try prefix match
  const prefixObjects = await findProteinsByPrefixSearch(uniprotName, fullName, dbxrefs, remainingFilters, input.page as number, limit)
  if (prefixObjects.length !== 0) {
    return prefixObjects
  }

  // try fuzzy match
  return await findProteinsByFuzzySearch(uniprotName, fullName, dbxrefs, remainingFilters, input.page as number, limit)
}

async function proteinSearch (input: paramsFormatType): Promise<any[]> {
  if ('protein_id' in input) {
    return await findProteinByID(input.protein_id as string)
  }

  if ('name' in input || 'uniprot_name' in input || 'uniprot_full_name' in input || 'dbxrefs' in input) {
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
