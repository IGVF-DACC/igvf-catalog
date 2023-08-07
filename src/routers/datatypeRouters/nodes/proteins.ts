import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'
import { RouterFuzzy } from '../../genericRouters/routerFuzzy'
import { paramsFormatType } from '../_helpers'

const schema = loadSchemaConfig()

export const proteinsQueryFormat = z.object({
  name: z.string().optional(),
  dbxrefs: z.string().optional(),
  page: z.number().default(0)
})

export const proteinFormat = z.object({
  _id: z.string(),
  name: z.string(),
  dbxrefs: z.array(z.string()).optional(),
  source: z.string(),
  source_url: z.string()
})

const schemaObj = schema.protein
const router = new RouterFilterBy(schemaObj)
const routerID = new RouterFilterByID(schemaObj)
const routerFuzzy = new RouterFuzzy(schemaObj)

async function conditionalSearch (input: paramsFormatType): Promise<any[]> {
  let params = { ...input, ...{ sort: 'chr' } }
  const exactMatch = await router.getObjects(params)

  if (input.dbxrefs !== undefined && exactMatch.length === 0) {
    const term = input.dbxrefs as string
    delete input.dbxrefs

    params = { ...input, ...{ sort: 'chr' } }
    return await routerFuzzy.getObjectsByFuzzyTextSearch(term, input.page as number, router.getFilterStatements(params))
  }

  return exactMatch
}

const proteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: router.apiSpecs.description } })
  .input(proteinsQueryFormat)
  .output(z.array(proteinFormat))
  .query(async ({ input }) => await conditionalSearch(input))

export const proteinID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${routerID.path}` } })
  .input(z.object({ id: z.string() }))
  .output(proteinFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))

export const proteinsRouters = {
  proteins,
  proteinID
}
