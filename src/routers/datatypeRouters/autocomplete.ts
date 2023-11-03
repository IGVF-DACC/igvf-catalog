import { publicProcedure } from '../../trpc'
import { RouterFuzzy } from '../genericRouters/routerFuzzy'
import { loadSchemaConfig } from '../genericRouters/genericRouters'
import { paramsFormatType } from './_helpers'
import { z } from 'zod'
import { descriptions } from './descriptions'

const schema = loadSchemaConfig()

const types = z.enum(['gene', 'ontology term', 'protein'])

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
  const routerFuzzy = new RouterFuzzy(schema[input.type as string])

  return await routerFuzzy.autocompleteSearch(input.term as string, input.page as number, true)
}

const autocomplete = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/autocomplete', description: descriptions.autocomplete } })
  .input(autocompleteQueryFormat)
  .output(z.array(autocompleteFormat))
  .query(async ({ input }) => await performAutocomplete(input))

export const autocompleteRouters = {
  autocomplete
}
