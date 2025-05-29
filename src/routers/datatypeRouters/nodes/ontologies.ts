import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { commonNodesParamsFormat } from '../params'

const MAX_PAGE_SIZE = 1000

const schema = loadSchemaConfig()
const ontologySchema = schema['ontology term']

const ontologySources = z.enum([
  'BAO',
  'Cellosaurus',
  'CHEBI',
  'CL',
  'CLO',
  'EFO',
  'ENCODE',
  'GO',
  'HPO',
  'MONDO',
  'NCIT',
  'OBA',
  'Oncotree',
  'ORPHANET',
  'UBERON',
  'VARIO'
])
const subontologies = z.enum([
  'biological_process',
  'cellular_component',
  'molecular_function'
])

export const ontologyQueryFormat = z.object({
  term_id: z.string().trim().optional(),
  name: z.string().trim().optional(),
  synonyms: z.string().optional(),
  description: z.string().trim().optional(),
  source: ontologySources.optional(),
  subontology: subontologies.optional()
}).merge(commonNodesParamsFormat).omit({ organism: true })

export const ontologyFormat = z.object({
  uri: z.string(),
  term_id: z.string(),
  name: z.string(),
  synonyms: z.array(z.string()).nullish(),
  description: z.string().nullish(),
  source: z.string().optional(),
  subontology: z.string().optional().nullable(),
  source_url: z.string().optional().nullable()
})

async function exactMatchSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  if (input.name !== undefined) {
    input.name = (input.name as string).toLowerCase().replaceAll('\'', '\\\'')
  }

  let filterBy = ''
  const filterSts = getFilterStatements(ontologySchema, input)
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }

  const query = `
    FOR record IN ${ontologySchema.db_collection_name as string}
    ${filterBy}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(ontologySchema)} }
  `
  const cursor = await db.query(query)
  return await cursor.all()
}

async function prefixMatchSearch (name: string, page: number, limit: number, filters: string): Promise<any[]> {
  const query = `
    FOR record IN ${ontologySchema.db_collection_name as string}
      FILTER STARTS_WITH(record.name, "${name}") ${filters ? `AND ${filters}` : ''}
      LIMIT ${page * limit}, ${limit}
      RETURN { ${getDBReturnStatements(ontologySchema)} }
  `
  return await (await db.query(query)).all()
}

async function fuzzyTextSearch (input: paramsFormatType): Promise<any[]> {
  const queryStatementsFuzzy = []
  const queryStatementsToken = []

  let name
  if (input.name !== undefined) {
    name = (input.name as string).toLowerCase()
    queryStatementsToken.push(`TOKENS("${decodeURIComponent(name)}", "text_en_no_stem") ALL in record.name`)
    queryStatementsFuzzy.push(`LEVENSHTEIN_MATCH(
      record.name,
      TOKENS("${decodeURIComponent(name)}", "text_en_no_stem")[0],
      1,    // max distance
      false // without transpositions
    )`)

    delete input.name
  }

  if (input.description !== undefined) {
    const description = (input.description as string).toLowerCase()

    queryStatementsToken.push(`TOKENS("${decodeURIComponent(description)}", "text_en_no_stem") ALL in record.description`)
    queryStatementsFuzzy.push(`LEVENSHTEIN_MATCH(
      record.description,
      TOKENS("${decodeURIComponent(description)}", "text_en_no_stem")[0],
      1,    // max distance
      false // without transpositions
    )`)

    delete input.description
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const filterSts = getFilterStatements(ontologySchema, input)

  if (name !== undefined) {
    const prefixObjects = await prefixMatchSearch(name, input.page as number, limit, filterSts)
    if (prefixObjects.length !== 0) {
      return prefixObjects
    }
  }

  let filterBy = ''
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }

  const searchViewName = `${ontologySchema.db_collection_name as string}_text_en_no_stem_inverted_search_alias`

  let objects: any[] = []

  for (const queryStatements of [queryStatementsToken, queryStatementsFuzzy]) {
    const query = `
      FOR record IN ${searchViewName}
      SEARCH ${queryStatements.join(' AND ')}
      ${filterBy}
      LIMIT ${input.page as number * limit}, ${limit}
      SORT BM25(record) DESC
      RETURN { ${getDBReturnStatements(ontologySchema)} }
    `

    objects = await (await db.query(query)).all()
    if (objects.length > 0) {
      break
    }
  }

  return objects
}

export async function ontologySearch (input: paramsFormatType): Promise<any[]> {
  const objects = await exactMatchSearch(input)

  if ((('name' in input && input.name !== undefined) || ('description' in input && input.description !== undefined)) && objects.length === 0) {
    return await fuzzyTextSearch(input)
  }

  return objects
}

export const ontologyTerm = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/ontology-terms', description: descriptions.ontology_terms } })
  .input(ontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await ontologySearch(input))

export const ontologyRouters = {
  ontologyTerm
}
