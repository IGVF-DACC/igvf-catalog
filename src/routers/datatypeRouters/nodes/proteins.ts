import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, probeThenFetchPage } from '../_helpers'
import { descriptions } from '../descriptions'
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
  uniprot_ids: z.array(z.string()).nullish(),
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

  return (await (await db.query(query)).all())
}

function exactMatchFilterClause (input: paramsFormatType): string {
  const workingInput = { ...input }
  const filters = []
  if (workingInput.name !== undefined) {
    const proteinName = workingInput.name as string
    delete workingInput.name
    filters.push(`"${decodeURIComponent(proteinName.toUpperCase())}" == record.name`)
  }
  if (workingInput.uniprot_name !== undefined) {
    const uniprotName = workingInput.uniprot_name as string
    delete workingInput.uniprot_name
    filters.push(`"${decodeURIComponent(uniprotName.toUpperCase())}" in record.uniprot_names`)
  }
  if (workingInput.uniprot_full_name !== undefined) {
    const fullName = workingInput.uniprot_full_name as string
    delete workingInput.uniprot_full_name
    filters.push(`"${decodeURIComponent(fullName)}" in record.uniprot_full_names`)
  }
  const additionalFilters = getFilterStatements(proteinSchema, workingInput)
  if (additionalFilters !== '') {
    filters.push(additionalFilters)
  }
  return filters.length > 0 ? `FILTER ${filters.join(' AND ')}` : ''
}

function exactMatchQueryBody (input: paramsFormatType, limitClause: string): string {
  return `
    FOR record IN ${proteinCollectionName}
    ${exactMatchFilterClause(input)}
    SORT record.chr
    ${limitClause}
    RETURN { ${getDBReturnStatements(proteinSchema)} }
  `
}

async function findProteins (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  const page = input.page as number
  const query = exactMatchQueryBody(input, `LIMIT ${page * limit}, ${limit}`)
  return await (await db.query(query)).all()
}

function searchViewQueryBody (
  buildMatch: (field: string, value: string) => string,
  fields: Record<string, string | undefined>,
  filters: string,
  limitClause: string
): string {
  const searchFilters = []
  for (const field in fields) {
    if (fields[field] !== undefined) {
      searchFilters.push(buildMatch(field, fields[field] as string))
    }
  }

  return `
    FOR record IN ${SEARCH_ALIAS}
    SEARCH ${searchFilters.join(' AND ')}
    ${filters}
    SORT BM25(record) DESC
    ${limitClause}
    RETURN { ${getDBReturnStatements(proteinSchema)} }
  `
}

// Each stage's applicability is decided by probeThenFetchPage via a page-independent
// existence probe (not "is page N empty"), so the same stage - and therefore a stable,
// non-overlapping result set - is used across every page of the same query. Previously,
// findProteins() also re-derived/deleted input.limit itself, which meant the exact-match
// stage silently ignored the caller-resolved limit (always falling back to QUERY_LIMIT)
// whenever it was reached from this text-search path.
async function findProteinsByTextSearch (input: paramsFormatType): Promise<any[]> {
  const uniprotName = input.uniprot_name as string | undefined
  const fullName = input.uniprot_full_name as string | undefined
  const dbxrefs = input.dbxrefs as string | undefined
  const name = input.name as string | undefined

  const nameOnlySearch = (name !== undefined || uniprotName !== undefined) && fullName === undefined && dbxrefs === undefined

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  const page = input.page as number

  const exactResults = await probeThenFetchPage((limitClause) => exactMatchQueryBody({ ...input }, limitClause), page, limit)
  if (exactResults !== null) {
    return exactResults
  }

  const remainingInput = { ...input }
  delete remainingInput.name
  delete remainingInput.uniprot_name
  delete remainingInput.uniprot_full_name
  delete remainingInput.dbxrefs
  let remainingFilters = getFilterStatements(proteinSchema, remainingInput)
  if (remainingFilters) {
    remainingFilters = `FILTER ${remainingFilters}`
  }

  const searchFields = { name, uniprot_names: uniprotName, uniprot_full_names: fullName, 'dbxrefs.id': dbxrefs }

  const prefixResults = await probeThenFetchPage(
    (limitClause) => searchViewQueryBody(
      (field, value) => `STARTS_WITH(record.${field}, TOKENS("${decodeURIComponent(value)}", 'text_en_no_stem'))`,
      searchFields,
      remainingFilters,
      limitClause
    ),
    page,
    limit
  )
  if (prefixResults !== null) {
    return prefixResults
  }

  if (nameOnlySearch) {
    return []
  }

  const fuzzyResults = await probeThenFetchPage(
    (limitClause) => searchViewQueryBody(
      (field, value) => `LEVENSHTEIN_MATCH(record.${field}, "${decodeURIComponent(value)}", 3, true)`,
      searchFields,
      remainingFilters,
      limitClause
    ),
    page,
    limit
  )
  return fuzzyResults ?? []
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
  .output(z.array(proteinFormat))
  .query(async ({ input }) => await proteinSearch(input))

export const proteinsRouters = {
  proteins
}
