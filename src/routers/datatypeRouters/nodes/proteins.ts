import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'

const schema = loadSchemaConfig()
const schemaObj = schema.protein

const proteinQueryFormat = z.object({
  name: z.string()
})

const proteinFormat = z.object({
  _id: z.string(),
  name: z.string(),
  source: z.string(),
  source_url: z.string()
})

const router = new RouterFilterBy(schemaObj)
const routerID = new RouterFilterByID(schemaObj)

export const proteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${router.apiName}`, description: router.apiSpecs.description } })
  .input(proteinQueryFormat)
  .output(z.array(proteinFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const proteinID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${routerID.path}`, description: router.apiSpecs.description } })
  .input(z.object({ id: z.string() }))
  .output(proteinFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))
