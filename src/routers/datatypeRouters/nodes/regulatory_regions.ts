import { z } from 'zod'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { paramsFormatType, preProcessRegionParam, getDBReturnStatements, getFilterStatements } from '../_helpers'
import { descriptions } from '../descriptions'
import { QUERY_LIMIT } from '../../../constants'

const HS_ZKD_INDEX = 'idx_1787383567561523200'
const MM_ZKD_INDEX = 'idx_1787385040709091328'
const MAX_PAGE_SIZE = 1000

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
  name: z.string(),
  biochemical_activity: z.string().nullable(),
  biochemical_activity_description: z.string().nullable(),
  type: z.string(),
  source: z.string(),
  source_url: z.string()
})

const humanSchemaObj = schema['regulatory region']
const mouseSchemaObj = schema['regulatory region mouse']

async function regulatoryRegionSearch (input: paramsFormatType): Promise<any[]> {
  let schema = humanSchemaObj
  let zkd_index = HS_ZKD_INDEX
  if (input.organism === 'mouse') {
    schema = mouseSchemaObj
    zkd_index = MM_ZKD_INDEX
  }
  delete input.organism

  let useIndex = ''
  if (input.region !== undefined) {
    useIndex = `OPTIONS { indexHint: "${zkd_index}", forceIndexHint: true }`
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const query = `
    FOR record IN ${schema.db_collection_name} ${useIndex}
    FILTER ${getFilterStatements(schema, preProcessRegionParam(input))}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(schema)} }
  `

  return await (await db.query(query)).all()
}

const regulatoryRegions = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/regulatory_regions', description: descriptions.regulatory_regions } })
  .input(regulatoryRegionsQueryFormat.merge(z.object({ limit: z.number().optional() })))
  .output(z.array(regulatoryRegionFormat))
  .query(async ({ input }) => await regulatoryRegionSearch(input))

export const regulatoryRegionRouters = {
  regulatoryRegions
}
