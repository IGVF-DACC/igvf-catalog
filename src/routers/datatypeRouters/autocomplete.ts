import { publicProcedure } from '../../trpc'
import { RouterFuzzy } from '../genericRouters/routerFuzzy'
import { loadSchemaConfig } from '../genericRouters/genericRouters'
import { paramsFormatType } from './_helpers'
import { z } from 'zod'
import { descriptions } from './descriptions'

const schema = loadSchemaConfig()

const types = z.enum(['gene', 'ontology term', 'protein', 'disease'])

const autocompleteQueryFormat = z.object({
  term: z.string(),
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
  const routerFuzzy = new RouterFuzzy(schema[schemaName])

  return await routerFuzzy.autocompleteSearch(input.term as string, input.page as number, true, customFilter)
}

const autocomplete = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/autocomplete', description: descriptions.autocomplete } })
  .input(autocompleteQueryFormat)
  .output(z.array(autocompleteFormat))
  .query(async ({ input }) => await performAutocomplete(input))

export const autocompleteRouters = {
  autocomplete
}
