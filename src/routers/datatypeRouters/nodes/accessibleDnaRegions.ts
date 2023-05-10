import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'

const schema = loadSchemaConfig()
const schemaObj = schema['accessible dna region']

const regionQueryFormat = z.object({
  chr: z.string().optional()
})

const regionFormat = z.object({
  _id: z.string(),
  chr: z.string(),
  start: z.string(),
  end: z.string(),
  source: z.string(),
  source_url: z.string()
})

const router = new RouterFilterBy(schemaObj)
const routerID = new RouterFilterByID(schemaObj)

export const accessibleDnaRegions = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${router.apiName}`, description: router.apiSpecs.description } })
  .input(regionQueryFormat)
  .output(z.array(regionFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const accessibleDnaRegionID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${routerID.path}`, description: router.apiSpecs.description } })
  .input(z.object({ id: z.string() }))
  .output(regionFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))
