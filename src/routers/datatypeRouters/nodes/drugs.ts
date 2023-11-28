import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'
import { RouterFuzzy } from '../../genericRouters/routerFuzzy'
import { paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

export const drugsQueryFormat = z.object({
  drug_id: z.string().trim().optional(),
  name: z.string().trim().optional()
})

export const drugFormat = z.object({
  _id: z.string(),
  drug_name: z.string(),
  drug_ontology_terms: z.array(z.string()).optional(),
  source: z.string(),
  source_url: z.string()
})

const schemaObj = schema.drug
const router = new RouterFilterBy(schemaObj)
const routerID = new RouterFilterByID(schemaObj)
const routerSearch = new RouterFuzzy(schemaObj)

async function drugSearch (input: paramsFormatType): Promise<any[]> {
  if (input.drug_id !== undefined) {
    return await routerID.getObjectById(input.drug_id as string)
  }

  const name = input.name as string
  // check fuzzy search (e.g. protein)
  const searchTerms = { drug_name: name }
  const textObjects = await routerSearch.textSearch(searchTerms, 'token', input.page as number)
  if (textObjects.length === 0) {
    return await routerSearch.textSearch(searchTerms, 'fuzzy', input.page as number)
  }
  return textObjects
}

const drugs = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: descriptions.drugs } })
  .input(drugsQueryFormat)
  .output(z.array(drugFormat).or(drugFormat))
  .query(async ({ input }) => await drugSearch(input))

export const drugsRouters = {
  drugs
}
