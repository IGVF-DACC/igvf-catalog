import { z } from 'zod'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { paramsFormatType, preProcessRegionParam, getDBReturnStatements, getFilterStatements } from '../_helpers'
import { descriptions } from '../descriptions'
import { QUERY_LIMIT } from '../../../constants'

export const HS_ZKD_INDEX = 'idx_1787383567561523200'
export const MM_ZKD_INDEX = 'idx_1787385040709091328'
const MAX_PAGE_SIZE = 1000

const schema = loadSchemaConfig()

const biochemicalActivity = z.enum([
  'CA',
  'CA-CTCF',
  'CA-H3K4me3',
  'CA-TF',
  'dELS',
  'ENH',
  'pELS',
  'PLS',
  'PRO',
  'TF'
])

const regulatoryRegionType = z.enum([
  'candidate_cis_regulatory_element',
  'accessible dna elements',
  'MPRA_tested_regulatory_element',
  'CRISPR_tested_element',
  'enhancer',
  'accessible dna elements (mouse)'
])

const regulatoryRegionSource = z.enum([
  'AFGR',
  'ENCODE-E2G',
  'ENCODE-E2G-CRISPR',
  'ENCODE_EpiRaction',
  'ENCODE_MPRA',
  'ENCODE_SCREEN (ccREs)',
  'FUNCODE',
  'PMID:34017130',
  'PMID:34038741'
])

export const regulatoryRegionsQueryFormat = z.object({
  organism: z.enum(['human', 'mouse']).default('human'),
  type: regulatoryRegionType.optional(),
  region: z.string().trim().optional(),
  biochemical_activity: biochemicalActivity.optional(),
  source: regulatoryRegionSource.optional(),
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

  let filterBy = ''
  const filterSts = getFilterStatements(schema, preProcessRegionParam(input))
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }

  const query = `
    FOR record IN ${schema.db_collection_name} ${useIndex}
    ${filterBy}
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
