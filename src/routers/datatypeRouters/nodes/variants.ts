import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'

const schema = loadSchemaConfig()
const schemaObj = schema['sequence variant']

const variantQueryFormat = z.object({
  rsid: z.string()
})

const variantFormat = z.object({
  _id: z.string(),
  chr: z.string(),
  pos: z.string(),
  rsid: z.string(),
  alt: z.string(),
  qual: z.string(),
  filter: z.string(),
  format: z.string()
})

const router = new RouterFilterBy(schemaObj)
const routerID = new RouterFilterByID(schemaObj)

export const variants = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${router.apiName}`, description: router.apiSpecs.description } })
  .input(variantQueryFormat)
  .output(z.array(variantFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const variantID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${routerID.path}`, description: router.apiSpecs.description } })
  .input(z.object({ id: z.string() }))
  .output(variantFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))
