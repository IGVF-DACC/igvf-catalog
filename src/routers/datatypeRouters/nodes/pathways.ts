import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { commonHumanNodesParamsFormat } from '../params'

const MAX_PAGE_SIZE = 500
const schema = loadSchemaConfig()
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

const pathwayFormat = z.object({
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

const pathwaySchema = schema.pathway

export async function pathwaySearch (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  if (input.id !== undefined) {
    input._key = input.id
    delete input.id
  }
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  const page = input.page ?? 0
  delete input.page
  let filterBy = ''
  const filterSts = getFilterStatements(pathwaySchema, input)
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }
  const query = `
    FOR record in ${pathwaySchema.db_collection_name as string}
    ${filterBy}
    SORT record._key
    LIMIT ${page as number * limit}, ${(page as number + 1) * limit}
    RETURN {
    ${getDBReturnStatements(pathwaySchema)}}
  `
  return await (await db.query(query)).all()
}

const pathways = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/pathways', description: descriptions.pathways } })
  .input(QueryFormat)
  .output(z.array(pathwayFormat))
  .query(async ({ input }) => await pathwaySearch(input))

export const pathwaysRouters = {
  pathways
}
