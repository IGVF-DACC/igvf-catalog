import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { geneFormat } from '../nodes/genes'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { regulatoryRegionFormat } from '../nodes/regulatory_regions'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonHumanEdgeParamsFormat, genesCommonQueryFormat, regulatoryRegionsCommonQueryFormat } from '../params'

const MAX_PAGE_SIZE = 500

const schema = loadSchemaConfig()
const regulatoryRegionToGeneSchema = schema['regulatory element to gene expression association']
const regulatoryRegionSchema = schema['regulatory region']
const geneSchema = schema.gene

const edgeSources = z.object({
  source: z.enum([
    'ENCODE_EpiRaction',
    'ENCODE-E2G-DNaseOnly',
    'ENCODE-E2G-Full',
    'ENCODE-E2G-CRISPR'
  ]).optional()
})

const regulatoryRegionType = z.enum([
  'candidate_cis_regulatory_element',
  'enhancer',
  'CRISPR_tested_element'
])

const biochemicalActivity = z.enum([
  'ENH',
  'PRO'
])

const regulatoryRegionToGeneFormat = z.object({
  score: z.number().nullable(),
  source: z.string().optional(),
  source_url: z.string().optional(),
  biological_context_name: z.string().nullable(),
  significant: z.boolean().nullish(),
  regulatory_region: z.string().or(regulatoryRegionFormat).optional(),
  gene: z.string().or(geneFormat).optional()
})

function edgeQuery (input: paramsFormatType): string {
  let query = ''

  if (input.source !== undefined) {
    query = `record.source == '${input.source}'`
    delete input.source
  }

  return query
}

const geneVerboseQuery = `
    FOR otherRecord IN ${geneSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(geneSchema).replaceAll('record', 'otherRecord')}}
  `

const regulatoryRegionVerboseQuery = `
  FOR otherRecord IN ${regulatoryRegionSchema.db_collection_name as string}
  FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
  RETURN {${getDBReturnStatements(regulatoryRegionSchema).replaceAll('record', 'otherRecord')}}
`
function validateGeneInput (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['gene_id', 'hgnc', 'name', 'alias'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one gene property must be defined.'
    })
  }
}

async function findRegulatoryRegionsFromGeneSearch (input: paramsFormatType): Promise<any[]> {
  validateGeneInput(input)
  delete input.organism
  if (input.gene_id !== undefined) {
    input._id = `genes/${input.gene_id}`
    delete input.gene_id
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let customFilter = edgeQuery(input)
  if (customFilter !== '') {
    customFilter = `and ${customFilter}`
  }

  const query = `
    LET targets = (
      FOR record IN ${geneSchema.db_collection_name as string}
      FILTER ${getFilterStatements(geneSchema, preProcessRegionParam(input))}
      RETURN record._id
    )

    FOR record IN ${regulatoryRegionToGeneSchema.db_collection_name as string}
      FILTER record._to IN targets ${customFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        ${getDBReturnStatements(regulatoryRegionToGeneSchema)},
        'biological_context_name': DOCUMENT(record.biological_context)['name'],
        'regulatory_region': ${input.verbose === 'true' ? `(${regulatoryRegionVerboseQuery})[0]` : 'record._from'},
        'gene': ${input.verbose === 'true' ? `(${geneVerboseQuery})[0]` : 'record._to'}
      }
  `
  return await (await db.query(query)).all()
}

async function findGenesFromRegulatoryRegionsSearch (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let customFilter = edgeQuery(input)
  if (customFilter !== '') {
    customFilter = `and ${customFilter}`
  }

  if (input.region === undefined) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Region must be defined.'
    })
  }

  const regulatoryRegionFilters = getFilterStatements(regulatoryRegionSchema, preProcessRegionParam(input))

  const query = `
    LET sources = (
      FOR record in ${regulatoryRegionSchema.db_collection_name as string}
      FILTER ${regulatoryRegionFilters}
      RETURN record._id
    )

    FOR record IN ${regulatoryRegionToGeneSchema.db_collection_name as string}
      FILTER record._from IN sources ${customFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        ${getDBReturnStatements(regulatoryRegionToGeneSchema)},
        'biological_context_name': DOCUMENT(record.biological_context)['name'],
        'gene': ${input.verbose === 'true' ? `(${geneVerboseQuery})[0]` : 'record._to'},
        'regulatory_region': ${input.verbose === 'true' ? `(${regulatoryRegionVerboseQuery})[0]` : 'record._from'},
      }
  `
  return await (await db.query(query)).all()
}

// eslint-disable-next-line @typescript-eslint/naming-convention
const genesQuery = genesCommonQueryFormat.merge(edgeSources).merge(commonHumanEdgeParamsFormat).transform(({ gene_name, ...rest }) => ({
  name: gene_name,
  ...rest
}))

const regulatoryRegionsQuery = regulatoryRegionsCommonQueryFormat.omit({
  region_type: true,
  biochemical_activity: true
}).merge(z.object({
  region_type: regulatoryRegionType.optional(),
  biochemical_activity: biochemicalActivity.optional()
// eslint-disable-next-line @typescript-eslint/naming-convention
})).merge(edgeSources).merge(commonHumanEdgeParamsFormat).transform(({ region_type, ...rest }) => ({
  type: region_type,
  ...rest
}))

const regulatoryRegionsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/regulatory_regions', description: descriptions.genes_regulatory_regions } })
  .input(genesQuery)
  .output(z.array(regulatoryRegionToGeneFormat))
  .query(async ({ input }) => await findRegulatoryRegionsFromGeneSearch(input))

const genesFromRegulatoryRegions = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/regulatory_regions/genes', description: descriptions.regulatory_regions_genes } })
  .input(regulatoryRegionsQuery)
  .output(z.array(regulatoryRegionToGeneFormat))
  .query(async ({ input }) => await findGenesFromRegulatoryRegionsSearch(input))

export const regulatoryRegionsGenesRouters = {
  regulatoryRegionsFromGenes,
  genesFromRegulatoryRegions
}
