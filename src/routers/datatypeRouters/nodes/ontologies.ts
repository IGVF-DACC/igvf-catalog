import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFuzzy } from '../../genericRouters/routerFuzzy'
import { paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

const ontologySources = z.enum([
  'UBERON',
  'CLO',
  'CL',
  'HPO',
  'MONDO',
  'GO',
  'EFO',
  'CHEBI',
  'VARIO',
  'Cellosaurus',
  'Oncotree',
  'ORPHANET',
  'NCIT'
])

export const ontologyQueryFormat = z.object({
  term_id: z.string().trim().optional(),
  name: z.string().trim().optional(),
  description: z.string().trim().optional(),
  source: ontologySources.optional(),
  subontology: z.string().trim().optional(),
  page: z.number().default(0)
})

export const ontologyFormat = z.object({
  uri: z.string(),
  term_id: z.string(),
  name: z.string(),
  description: z.string().nullable(),
  source: z.string().optional(),
  subontology: z.string().optional().nullable()
})

const schemaObj = schema['ontology term']
const router = new RouterFilterBy(schemaObj)
const routerSearch = new RouterFuzzy(schemaObj)

async function ontologySearch (input: paramsFormatType): Promise<any[]> {
  input.sort = '_key'

  const objects = await router.getObjects(input)

  if (('term_name' in input || 'description' in input) && objects.length === 0) {
    const termName = input.name as string
    delete input.name

    const description = input.description as string
    delete input.description

    const remainingFilters = router.getFilterStatements(input)

    const searchTerms = { name: termName, description }
    const textObjects = await routerSearch.textSearch(searchTerms, 'token', input.page as number, remainingFilters)
    if (textObjects.length === 0) {
      return await routerSearch.textSearch(searchTerms, 'fuzzy', input.page as number, remainingFilters)
    }
    return textObjects
  }

  return objects
}

export const ontologyTerm = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: descriptions.ontology_terms } })
  .input(ontologyQueryFormat)
  .output(z.array(ontologyFormat))
  .query(async ({ input }) => await ontologySearch(input))

export const ontologyRouters = {
  ontologyTerm
}
