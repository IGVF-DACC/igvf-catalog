import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFuzzy } from '../../genericRouters/routerFuzzy'
import { paramsFormatType } from '../_helpers'

const schema = loadSchemaConfig()

export const ontologyQueryFormat = z.object({
  term_id: z.string().optional(),
  term_name: z.string().optional(),
  source: z.string().optional(),
  subontology: z.string().optional(),
  page: z.number().default(0)
})

export const ontologyFormat = z.object({
  uri: z.string(),
  term_id: z.string(),
  term_name: z.string(),
  description: z.string().nullable(),
  source: z.string().optional(),
  subontology: z.string().optional()
})

const schemaObj = schema['ontology term']
const router = new RouterFilterBy(schemaObj)
const routerSearch = new RouterFuzzy(schemaObj)

async function ontologySearch (input: paramsFormatType): Promise<any[]> {
  input.sort = '_key'

  const objects = await router.getObjects(input)

  if ('term_name' in input && objects.length === 0) {
    const searchTerm = input.term_name as string
    delete input.term_name
    const remainingFilters = router.getFilterStatements(input)

    const textObjects = await routerSearch.getObjectsByMultipleTokenMatch(searchTerm, input.page as number, remainingFilters)
    if (textObjects.length === 0) {
      return await routerSearch.getObjectsByFuzzyTextSearch(searchTerm, input.page as number, remainingFilters)
    }
    return textObjects
  }

  return objects
}

export const ontologyTerm = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: router.apiSpecs.description } })
  .input(ontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await ontologySearch(input))

export const ontologyRouters = {
  ontologyTerm
}
