import { z } from 'zod'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, probeThenFetchPage } from '../_helpers'
import { descriptions } from '../descriptions'
import { commonNodesParamsFormat } from '../params'
import { getSchema, getCollectionEnumValuesOrThrow } from '../schema'

const MAX_PAGE_SIZE = 1000

const ontologySchema = getSchema('data/schemas/nodes/ontology_terms.Ontology.json')
const ontologyCollectionName = 'ontology_terms'

const ontologySources = getCollectionEnumValuesOrThrow('nodes', 'ontology_terms', 'source')
const subontologies = getCollectionEnumValuesOrThrow('nodes', 'ontology_terms', 'subontology')

export const ontologyQueryFormat = z.object({
  term_id: z.string().trim().optional(),
  name: z.string().trim().optional(),
  synonyms: z.string().optional(),
  source: z.enum(ontologySources).optional(),
  subontology: z.enum(subontologies).optional(),
  files_fileset: z.string().optional()
}).merge(commonNodesParamsFormat).omit({ organism: true })

export const ontologyFormat = z.object({
  uri: z.string(),
  term_id: z.string(),
  name: z.string(),
  synonyms: z.array(z.string()).nullish(),
  description: z.string().nullish(),
  source: z.string().optional(),
  subontology: z.string().optional().nullable(),
  source_url: z.string().optional().nullable(),
  class: z.string().nullish(),
  method: z.string().nullish(),
  files_filesets: z.string().nullish()
})

function exactMatchQueryBody (input: paramsFormatType, limitClause: string): string {
  const filterSts = getFilterStatements(ontologySchema, input)
  const filterBy = filterSts !== '' ? `FILTER ${filterSts}` : ''
  return `
    FOR record IN ${ontologyCollectionName}
    ${filterBy}
    SORT record._key
    ${limitClause}
    RETURN { ${getDBReturnStatements(ontologySchema)} }
  `
}

function prefixMatchQueryBody (name: string, filters: string, limitClause: string): string {
  return `
    FOR record IN ${ontologyCollectionName}
      FILTER STARTS_WITH(record.name, "${name}") ${filters ? `AND ${filters}` : ''}
      SORT record._key
      ${limitClause}
      RETURN { ${getDBReturnStatements(ontologySchema)} }
  `
}

function searchViewQueryBody (searchClause: string, filterBy: string, limitClause: string): string {
  const searchViewName = `${ontologyCollectionName}_text_en_no_stem_inverted_search_alias`
  return `
    FOR record IN ${searchViewName}
    SEARCH ${searchClause}
    ${filterBy}
    SORT BM25(record) DESC, record._key
    ${limitClause}
    RETURN { ${getDBReturnStatements(ontologySchema)} }
  `
}

// Each stage's applicability is decided by probeThenFetchPage via a page-independent
// existence probe (not "is page N empty"), so the same stage - and therefore a stable,
// non-overlapping result set - is used across every page of the same query. See
// probeThenFetchPage's own comment in _helpers.ts for why that distinction matters.
export async function ontologySearch (input: paramsFormatType): Promise<any[]> {
  if (input.files_fileset !== undefined) {
    input.files_filesets = `files_filesets/${input.files_fileset as string}`
    delete input.files_fileset
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  const page = input.page as number
  const rawName = input.name as string | undefined

  const exactInput = { ...input }
  if (exactInput.name !== undefined) {
    exactInput.name = (exactInput.name as string).toLowerCase().replaceAll('\'', '\\\'')
  }
  const exactResults = await probeThenFetchPage((limitClause) => exactMatchQueryBody(exactInput, limitClause), page, limit)
  if (exactResults !== null) {
    return exactResults
  }

  if (rawName === undefined) {
    return []
  }

  const name = rawName.toLowerCase()
  const remainingInput = { ...input }
  delete remainingInput.name
  const filterSts = getFilterStatements(ontologySchema, remainingInput)

  const prefixResults = await probeThenFetchPage((limitClause) => prefixMatchQueryBody(name, filterSts, limitClause), page, limit)
  if (prefixResults !== null) {
    return prefixResults
  }

  const filterBy = filterSts !== '' ? `FILTER ${filterSts}` : ''

  const tokenSearchClause = `TOKENS("${decodeURIComponent(name)}", "text_en_no_stem") ALL in record.name`
  const tokenResults = await probeThenFetchPage((limitClause) => searchViewQueryBody(tokenSearchClause, filterBy, limitClause), page, limit)
  if (tokenResults !== null) {
    return tokenResults
  }

  const fuzzySearchClause = `LEVENSHTEIN_MATCH(
    record.name,
    TOKENS("${decodeURIComponent(name)}", "text_en_no_stem")[0],
    1,    // max distance
    false // without transpositions
  )`
  const fuzzyResults = await probeThenFetchPage((limitClause) => searchViewQueryBody(fuzzySearchClause, filterBy, limitClause), page, limit)
  return fuzzyResults ?? []
}

export const ontologyTerm = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/ontology-terms', description: descriptions.ontology_terms } })
  .input(ontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await ontologySearch(input))

export const ontologyRouters = {
  ontologyTerm
}
