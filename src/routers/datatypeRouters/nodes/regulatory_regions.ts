import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { preProcessRegionParam } from '../_helpers'

const schema = loadSchemaConfig()

const regulatoryRegionsQueryFormat = z.object({
  type: z.enum(['candidate_cis_regulatory_element']).optional(),
  region: z.string().optional(),
  biochemical_activity: z.string().optional(),
  source: z.string().optional(),
  page: z.number().default(0)
})

const regulatoryRegionFormat = z.object({
  chr: z.string(),
  start: z.number(),
  end: z.number(),
  biochemical_activity: z.string().nullable(),
  biochemical_activity_description: z.string().nullable(),
  type: z.string(),
  source: z.string(),
  source_url: z.string()
})

const schemaObj = schema['regulatory region']
const router = new RouterFilterBy(schemaObj)

const regulatoryRegions = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: router.apiSpecs.description } })
  .input(regulatoryRegionsQueryFormat)
  .output(z.array(regulatoryRegionFormat))
  .query(async ({ input }) => await router.getObjects(preProcessRegionParam(input)))

export const regulatoryRegionRouters = {
  regulatoryRegions
}
