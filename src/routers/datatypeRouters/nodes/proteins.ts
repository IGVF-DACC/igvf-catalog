import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'
import { RouterFuzzy } from '../../genericRouters/routerFuzzy'
import { paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

export const proteinsQueryFormat = z.object({
  protein_id: z.string().trim().optional(),
  name: z.string().trim().optional(),
  full_name: z.string().trim().optional(),
  dbxrefs: z.string().trim().optional(),
  page: z.number().default(0)
})
const dbxrefFormat = z.object({ name: z.string(), id: z.string() })

export const proteinFormat = z.object({
  _id: z.string(),
  name: z.string(),
  full_name: z.string().optional(),
  dbxrefs: z.array(dbxrefFormat).optional(),
  source: z.string(),
  source_url: z.string()
})

const schemaObj = schema.protein
const router = new RouterFilterBy(schemaObj)
const routerID = new RouterFilterByID(schemaObj)
const routerSearch = new RouterFuzzy(schemaObj)

async function proteinSearch (input: paramsFormatType): Promise<any[]> {
  if (input.protein_id !== undefined) {
    return await routerID.getObjectById(input.protein_id as string)
  }

  if ('name' in input || 'full_name' in input || 'dbxrefs' in input) {
    const name = input.name as string
    delete input.name
    const fullName = input.full_name as string
    delete input.full_name
    const dbxrefs = input.dbxrefs as string
    delete input.dbxrefs
    const remainingFilters = router.getFilterStatements(input)
    const searchTerms = { name, full_name: fullName, 'dbxrefs.id': dbxrefs }
    let textObjects = await routerSearch.textSearch(searchTerms, 'token', input.page as number, remainingFilters)
    if (textObjects.length === 0) {
      if (searchTerms['dbxrefs.id'] !== undefined) {
        textObjects = await routerSearch.textSearch(searchTerms, 'autocomplete', input.page as number, remainingFilters)
      } else {
        textObjects = await routerSearch.textSearch(searchTerms, 'fuzzy', input.page as number, remainingFilters)
      }
    }
    return textObjects
  }

  const params = { ...input, ...{ sort: 'chr' } }
  return await router.getObjects(params)
}

const proteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: descriptions.proteins } })
  .input(proteinsQueryFormat)
  .output(z.array(proteinFormat).or(proteinFormat))
  .query(async ({ input }) => await proteinSearch(input))

export const proteinsRouters = {
  proteins
}
