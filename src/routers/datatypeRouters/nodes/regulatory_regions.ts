import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

const regulatoryRegionsQueryFormat = z.object({
  region: z.string().optional(),
  biochemical_activity: z.string().optional(),
  source: z.string().optional(),
  page: z.number().default(0)
})

const regulatoryRegionsByTypeQueryFormat = z.object({
  region: z.string().optional(),
  biochemical_activity: z.string().optional(),
  source: z.string().optional(),
  page: z.number().default(0),
  type: z.enum(['candidate_cis_regulatory_element'])
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
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: descriptions.regulatory_regions } })
  .input(regulatoryRegionsQueryFormat)
  .output(z.array(regulatoryRegionFormat))
  .query(async ({ input }) => await router.getObjects(preProcessRegionParam(input)))

const regulatoryRegionsByCandidateCis = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}/{type}`, description: descriptions.regulatory_regions_type } })
  .input(regulatoryRegionsByTypeQueryFormat)
  .output(z.array(regulatoryRegionFormat))
  .query(async ({ input }) => await router.getObjects(preProcessRegionParam(input)))

export const regulatoryRegionRouters = {
  regulatoryRegions,
  regulatoryRegionsByCandidateCis
}
