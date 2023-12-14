import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { regulatoryRegionsQueryFormat, regulatoryRegionFormat } from './regulatory_regions'

const schema = loadSchemaConfig()
const schemaObj = schema['regulatory region mouse']
const router = new RouterFilterBy(schemaObj)

const mmRegulatoryRegions = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: descriptions.mm_regulatory_regions } })
  .input(regulatoryRegionsQueryFormat)
  .output(z.array(regulatoryRegionFormat))
  .query(async ({ input }) => await router.getObjects(preProcessRegionParam(input)))

export const mmRegulatoryRegionRouters = {
  mmRegulatoryRegions
}
