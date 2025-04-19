import { publicProcedure } from '../../trpc'
import { RouterFuzzy } from '../genericRouters/routerFuzzy'
import { loadSchemaConfig } from '../genericRouters/genericRouters'
import { getDBReturnStatements, paramsFormatType } from './_helpers'
import { QUERY_LIMIT } from '../../constants'
import { z } from 'zod'
import { descriptions } from './descriptions'
import { db } from '../../database'

const schema = loadSchemaConfig()

const types = z.enum(['gene', 'ontology term', 'protein', 'disease'])

const autocompleteQueryFormat = z.object({
  term: z.string().trim(),
  type: types,
  page: z.number().default(0).optional()
})

const autocompleteFormat = z.object({
  term: z.string(),
  uri: z.string()
})

async function performAutocomplete (input: paramsFormatType): Promise<any[]> {
  let schemaName = input.type as string
  let customFilter = ''
  if (input.type === 'disease') {
    schemaName = 'ontology term'
    customFilter = 'record.source == \'ORPHANET\''
  }

  const schema = loadSchemaConfig()[schemaName]

  const searchField = this.apiSpecs.fuzzy_text_search?.split(',').map((item: string) => item.trim()) || []

  const query = `
    FOR record IN ${`${schema.db_collection_name as string}_text_en_no_stem_inverted_search_alias`}
      SEARCH STARTS_WITH(record['${searchField}'], "${input.term as string}")
      SORT BM25(record) DESC
      ${customFilter}
      LIMIT ${input.page as number * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN { term: record['${searchField}'], uri: CONCAT('/${this.apiName}/', record['_key']) }
  `
  return await (await db.query(query)).all()
}

const autocomplete = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/autocomplete', description: descriptions.autocomplete } })
  .input(autocompleteQueryFormat)
  .output(z.array(autocompleteFormat))
  .query(async ({ input }) => await performAutocomplete(input))

export const autocompleteRouters = {
  autocomplete
}
