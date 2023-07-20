import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'

const schema = loadSchemaConfig()

const proteinsQueryFormat = z.object({
  name: z.string().optional(),
  page: z.number().default(0)
})

const proteinFormat = z.object({
  _id: z.string(),
  name: z.string(),
  dbxrefs: z.array(z.string()).optional(),
  source: z.string(),
  source_url: z.any()
})

const schemaObj = schema.protein
const router = new RouterFilterBy(schemaObj)
const routerID = new RouterFilterByID(schemaObj)

const proteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: router.apiSpecs.description } })
  .input(proteinsQueryFormat)
  .output(z.array(proteinFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const proteinID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${routerID.path}` } })
  .input(z.object({ id: z.string() }))
  .output(proteinFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))

export const proteinsRouters = {
  proteins,
  proteinID
}
