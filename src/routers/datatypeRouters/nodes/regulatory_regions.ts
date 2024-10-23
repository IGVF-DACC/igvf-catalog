import { z } from 'zod'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { paramsFormatType, preProcessRegionParam, getDBReturnStatements, getFilterStatements } from '../_helpers'
import { descriptions } from '../descriptions'
import { QUERY_LIMIT } from '../../../constants'
import { biochemicalActivity, commonNodesParamsFormat, regulatoryRegionSource, regulatoryRegionType } from '../params'

export const HS_ZKD_INDEX = 'idx_1787383567561523200'
export const MM_ZKD_INDEX = 'idx_1787385040709091328'
const MAX_PAGE_SIZE = 1000

const schema = loadSchemaConfig()

export const regulatoryRegionsQueryFormat = z.object({
  region: z.string().trim().optional(),
  biochemical_activity: biochemicalActivity.optional(),
  type: regulatoryRegionType.optional(),
  source: regulatoryRegionSource.optional()
}).merge(commonNodesParamsFormat)

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
  let zkdIndex = HS_ZKD_INDEX
  if (input.organism === 'Mus musculus') {
    schema = mouseSchemaObj
    zkdIndex = MM_ZKD_INDEX
  }
  delete input.organism

  let useIndex = ''
  if (input.region !== undefined) {
    useIndex = `OPTIONS { indexHint: "${zkdIndex}", forceIndexHint: true }`
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filterBy = ''
  const filterSts = getFilterStatements(schema, preProcessRegionParam(input))
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }

  const query = `
    FOR record IN ${schema.db_collection_name as string} ${useIndex}
    ${filterBy}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(schema)} }
  `

  return await (await db.query(query)).all()
}

const regulatoryRegions = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/regulatory-regions', description: descriptions.regulatory_regions } })
  .input(regulatoryRegionsQueryFormat.merge(z.object({ limit: z.number().optional() })))
  .output(z.array(regulatoryRegionFormat))
  .query(async ({ input }) => await regulatoryRegionSearch(input))

export const regulatoryRegionRouters = {
  regulatoryRegions
}
