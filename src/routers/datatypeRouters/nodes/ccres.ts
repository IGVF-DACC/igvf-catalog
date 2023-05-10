import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'

const schema = loadSchemaConfig()
const schemaObj = schema['ccre regulatory region']

const ccreQueryFormat = z.object({
  chr: z.string().optional(),
  biochemical_activity: z.string().optional()
})

const ccreFormat = z.object({
  _id: z.string(),
  chr: z.string(),
  start: z.string(),
  end: z.string(),
  biochemical_activity: z.string(),
  biochemical_activity_description: z.string(),
  type: z.string(),
  source: z.string(),
  source_url: z.string()
})

const router = new RouterFilterBy(schemaObj)
const routerID = new RouterFilterByID(schemaObj)

export const ccres = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${router.apiName}`, description: router.apiSpecs.description } })
  .input(ccreQueryFormat)
  .output(z.array(ccreFormat))
  .query(async ({ input }) => await router.getObjects(input))

export const ccreID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/new_${routerID.path}`, description: router.apiSpecs.description } })
  .input(z.object({ id: z.string() }))
  .output(ccreFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))
