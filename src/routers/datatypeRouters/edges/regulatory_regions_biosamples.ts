import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { paramsFormatType } from '../_helpers'
import { ontologyFormat } from '../nodes/ontologies'
import { regulatoryRegionFormat, regulatoryRegionsQueryFormat } from '../nodes/regulatory_regions'
import { TRPCError } from '@trpc/server'
import { descriptions } from '../descriptions'

// only have one type in this edge collection right now
const edgeTypes = z.object({
  type: z.enum([
    'MPRA_expression_tested'
  ]).optional()
})

function edgeQuery (input: paramsFormatType): string {
  const query = []

  if (input.type !== undefined) {
    query.push(`record.type == '${input.type}'`)
    delete input.type
  }

  return query.join('and ')
}

const regulatoryRegionToBiosampleFormat = z.object({
  'regulatory region': z.string().or(z.array(regulatoryRegionFormat)).optional(),
  activity_score: z.number().nullable(),
  source: z.string().optional(),
  source_url: z.string().optional(),
  'ontology term': z.string().or(z.array(ontologyFormat)).optional()
})

const schema = loadSchemaConfig()

const schemaObj = schema['regulatory element to biosample']
const router = new RouterEdges(schemaObj)

async function conditionalBiosampleSearch (input: paramsFormatType): Promise<any[]> {
  if (Object.keys(input).filter(item => !['term_id', 'term_name'].includes(item)).length === 0) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one gene property must be defined.'
    })
  }

  if (input.term_id !== undefined) {
    input._to = `ontology_terms/${input.term_id}`
    delete input.term_id
    input.sort = '_key'
    return await router.getEdgeObjects(input, '', input.verbose === 'true')
  }

  return await router.getTargetEdgesByTokenTextSearch(input, 'term_name', input.verbose === 'true')
}

const biosamplesFromRegulatoryRegions = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/regulatory_regions/biosamples', description: descriptions.regulatory_regions_biosamples } })
  .input(regulatoryRegionsQueryFormat.omit({ organism: true, biochemical_activity: true }).merge(edgeTypes).merge((z.object({ verbose: z.enum(['true', 'false']).default('false') }))))
  .output(z.array(regulatoryRegionToBiosampleFormat))
  .query(async ({ input }) => await router.getTargetsWithEdgeFilter(input, '_key', '', input.verbose === 'true', edgeQuery(input)))

const regulatoryRegionsFromBiosamples = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/biosamples/regulatory_regions', description: descriptions.biosamples_regulatory_regions } })
  .input(edgeTypes.merge(z.object({ term_id: z.string().trim().optional(), term_name: z.string().trim().optional(), page: z.number().default(0), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(regulatoryRegionToBiosampleFormat))
  .query(async ({ input }) => await conditionalBiosampleSearch(input))

export const regulatoryRegionsBiosamplesRouters = {
  biosamplesFromRegulatoryRegions,
  regulatoryRegionsFromBiosamples
}
