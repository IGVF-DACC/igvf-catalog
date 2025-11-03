import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { commonHumanNodesParamsFormat } from '../params'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 500
const pathwaySchema = getSchema('data/schemas/nodes/pathways.ReactomePathway.json')
const pathwayCollectionName = (pathwaySchema.accessible_via as Record<string, any>).name as string
const QueryFormat = z.object({
  id: z.string().trim().optional(),
  name: z.string().trim().optional(),
  is_in_disease: z.preprocess((arg) => {
    if (typeof arg === 'string') {
      if (arg === 'true') {
        return true
      }
      return false
    }
    return arg
  }, z.boolean()).optional(),
  name_aliases: z.string().trim().optional(),
  is_top_level_pathway: z.preprocess((arg) => {
    if (typeof arg === 'string') {
      if (arg === 'true') {
        return true
      }
      return false
    }
    return arg
  }, z.boolean()).optional(),
  disease_ontology_terms: z.string().trim().optional(),
  go_biological_process: z.string().trim().optional()
}).merge(commonHumanNodesParamsFormat)

export const pathwayFormat = z.object({
  _id: z.string(),
  name: z.string(),
  organism: z.string(),
  source: z.string(),
  source_url: z.string(),
  id_version: z.string(),
  is_in_disease: z.boolean(),
  name_aliases: z.array(z.string()),
  is_top_level_pathway: z.boolean(),
  disease_ontology_terms: z.array(z.string()).nullable(),
  go_biological_process: z.string().nullable()
})

export async function findPathwaysByTextSearch (input: paramsFormatType, schema: any): Promise<any[]> {
  if (input.limit !== undefined) {
    input.limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
  } else {
    input.limit = QUERY_LIMIT
  }
  const name = input.name
  delete input.name
  const nameAlias = input.name_aliases
  delete input.name_aliases
  let remainingFilters = getFilterStatements(schema, input)
  if (remainingFilters) {
    remainingFilters = `FILTER ${remainingFilters}`
  }
  const query = (searchFilters: string[]): string => {
    return `
      FOR record IN ${pathwayCollectionName}_text_en_no_stem_inverted_search_alias
        SEARCH ${searchFilters.join(' AND ')}
        ${remainingFilters}
        LIMIT ${input.page as number * (input.limit as number)}, ${input.limit as number}
        SORT BM25(record) DESC
        RETURN { ${getDBReturnStatements(pathwaySchema)} }
    `
  }
  let searchFilters = []
  if (name !== undefined) {
    searchFilters.push(`TOKENS("${decodeURIComponent(name as string)}", "text_en_no_stem") ALL in record.name`)
  }
  if (nameAlias !== undefined) {
    searchFilters.push(`TOKENS("${decodeURIComponent(nameAlias as string)}", "text_en_no_stem") ALL in record.name_aliases`)
  }
  const textObjects = await (await db.query(query(searchFilters))).all()
  if (textObjects.length === 0) {
    searchFilters = []
    if (name !== undefined) {
      searchFilters.push(`LEVENSHTEIN_MATCH(record.name, TOKENS("${decodeURIComponent(name as string)}", "text_en_no_stem")[0], 1, false)`)
    }
    if (nameAlias !== undefined) {
      searchFilters.push(`LEVENSHTEIN_MATCH(record.alias, TOKENS("${decodeURIComponent(nameAlias as string)}", "text_en_no_stem")[0], 1, false)`)
    }
    return await (await db.query(query(searchFilters))).all()
  }
  return textObjects
}

export async function pathwaySearchPersistent (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  if (input.id !== undefined) {
    input._key = input.id
    delete input.id
  }
  if (input.limit !== undefined) {
    input.limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
  } else {
    input.limit = QUERY_LIMIT
  }
  if (input.disease_ontology_terms !== undefined) {
    input.disease_ontology_terms = `ontology_terms/${input.disease_ontology_terms as string}`
  }
  if (input.go_biological_process !== undefined) {
    input.go_biological_process = `ontology_terms/${input.go_biological_process as string}`
  }
  let filterBy = ''
  const filterSts = getFilterStatements(pathwaySchema, input)
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }
  const query = `
    FOR record in ${pathwayCollectionName}
    ${filterBy}
    SORT record._key
    LIMIT ${input.page as number * input.limit}, ${input.limit}
    RETURN {
    ${getDBReturnStatements(pathwaySchema)}}
  `
  return await (await db.query(query)).all()
}

export async function pathwaySearch (input: paramsFormatType): Promise<any[]> {
  const pathways = await pathwaySearchPersistent(input)
  if (pathways.length !== 0) {
    return pathways
  }
  if (('name' in input && input.name !== undefined) || ('name_aliases' in input && input.name_aliases !== undefined)) {
    return await findPathwaysByTextSearch(input, pathwaySchema)
  }
  return []
}

const pathways = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/pathways', description: descriptions.pathways } })
  .input(QueryFormat)
  .output(z.array(pathwayFormat))
  .query(async ({ input }) => await pathwaySearch(input))

export const pathwaysRouters = {
  pathways
}
