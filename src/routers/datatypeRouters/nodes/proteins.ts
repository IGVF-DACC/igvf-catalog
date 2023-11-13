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
  protein_id: z.string().optional(),
  name: z.string().optional(),
  full_name: z.string().optional(),
  dbxrefs: z.string().optional(),
  page: z.number().default(0)
})

export const proteinFormat = z.object({
  _id: z.string(),
  name: z.string(),
  full_name: z.string().optional(),
  dbxrefs: z.array(z.string()).optional(),
  source: z.string(),
  source_url: z.string()
})

const schemaObj = schema.protein
const router = new RouterFilterBy(schemaObj)
const routerID = new RouterFilterByID(schemaObj)
const routerFuzzy = new RouterFuzzy(schemaObj)

async function proteinSearch (input: paramsFormatType): Promise<any[]> {
  if (input.protein_id !== undefined) {
    return await routerID.getObjectById(input.protein_id as string)
  }

  let params = { ...input, ...{ sort: 'chr' } }
  const exactMatch = await router.getObjects(params)

  if (input.name !== undefined && exactMatch.length === 0) {
    const term = input.name as string
    delete input.name

    params = { ...input, ...{ sort: 'chr' } }
    return await routerFuzzy.autocompleteSearch(term, input.page as number, false, router.getFilterStatements(params))
  }

  return exactMatch
}

const proteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: descriptions.proteins } })
  .input(proteinsQueryFormat)
  .output(z.array(proteinFormat).or(proteinFormat))
  .query(async ({ input }) => await proteinSearch(input))

export const proteinsRouters = {
  proteins
}
