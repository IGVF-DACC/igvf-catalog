import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

export const regulatoryRegionsQueryFormat = z.object({
  organism: z.enum(['human', 'mouse']).default('human'),
  type: z.enum(['candidate_cis_regulatory_element', 'accessible dna elements', 'MPRA_tested_regulatory_element', 'accessible dna elements (mouse)']).optional(),
  region: z.string().trim().optional(),
  biochemical_activity: z.string().trim().optional(),
  source: z.string().trim().optional(),
  page: z.number().default(0)
})

export const regulatoryRegionFormat = z.object({
  chr: z.string(),
  start: z.number(),
  end: z.number(),
  biochemical_activity: z.string().nullable(),
  biochemical_activity_description: z.string().nullable(),
  type: z.string(),
  source: z.string(),
  source_url: z.string()
})

const humanSchemaObj = schema['regulatory region']
const humanRouter = new RouterFilterBy(humanSchemaObj)

const mouseSchemaObj = schema['regulatory region mouse']
const mouseRouter = new RouterFilterBy(mouseSchemaObj)

async function regulatoryRegionSearch (input: paramsFormatType): Promise<any[]> {
  let router = humanRouter

  if (input.organism === 'mouse') {
    router = mouseRouter
  }

  delete input.organism

  return await router.getObjects(preProcessRegionParam(input))
}

const regulatoryRegions = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/regulatory_regions', description: descriptions.regulatory_regions } })
  .input(regulatoryRegionsQueryFormat)
  .output(z.array(regulatoryRegionFormat))
  .query(async ({ input }) => await regulatoryRegionSearch(preProcessRegionParam(input)))

export const regulatoryRegionRouters = {
  regulatoryRegions
}
