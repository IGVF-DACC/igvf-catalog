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
import { commonHumanEdgeParamsFormat, commonNodesParamsFormat, regulatoryRegionsCommonQueryFormat } from '../params'

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

const regionFromGeneFormat = z.object({
  gene: z.object({
    name: z.string(),
    id: z.string(),
    start: z.number(),
    end: z.number(),
    chr: z.string()
  }),
  regions: z.array(z.object({
    id: z.string(),
    cell_type: z.string(),
    score: z.number(),
    model: z.string(),
    dataset: z.string(),
    enhancer_type: z.string(),
    enhancer_start: z.number(),
    enhancer_end: z.number()
  }))
}).or(z.object({}))

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

async function findRegulatoryRegionsFromGene (input: paramsFormatType): Promise<any[]> {
  if (input.gene_id === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'gene_id must be specified.'
    })
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const query = `
    LET gene = (
      FOR geneRecord IN genes
      FILTER geneRecord._id == 'genes/${input.gene_id as string}'
      RETURN {
        name: geneRecord.name,
        id: geneRecord._id,
        start: geneRecord['start:long'],
        end: geneRecord['end:long'],
        chr: geneRecord.chr
      }
    )[0]

    LET regions = (
      FOR record IN ${regulatoryRegionToGeneSchema.db_collection_name as string}
      FILTER record._to == 'genes/${input.gene_id as string}'
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      LET regulatoryRegion = (
        FOR otherRecord IN regulatory_regions
        FILTER otherRecord._id == record._from
        RETURN { type: otherRecord.type, start: otherRecord['start:long'], end: otherRecord['end:long'] }
      )[0]

      RETURN {
        'id': record._from,
        'cell_type': DOCUMENT(record.biological_context)['name'],
        'score': record['score:long'],
        'model': record.source,
        'dataset': record.source_url,
        'enhancer_type': regulatoryRegion.type,
        'enhancer_start': regulatoryRegion.start,
        'enhancer_end': regulatoryRegion.end
      }
    )

    RETURN (gene != NULL ? { 'gene': gene, 'regions': regions }: {})
  `

  return (await (await db.query(query)).all())[0]
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
  .meta({ openapi: { method: 'GET', path: '/genes/regulatory_regions', description: descriptions.genes_predictions } })
  .input(z.object({ gene_id: z.string() }).merge(commonNodesParamsFormat).omit({ organism: true }))
  .output(regionFromGeneFormat)
  .query(async ({ input }) => await findRegulatoryRegionsFromGene(input))

const genesFromRegulatoryRegions = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/regulatory_regions/genes', description: descriptions.regulatory_regions_genes } })
  .input(regulatoryRegionsQuery)
  .output(z.array(regulatoryRegionToGeneFormat))
  .query(async ({ input }) => await findGenesFromRegulatoryRegionsSearch(input))

export const regulatoryRegionsGenesRouters = {
  regulatoryRegionsFromGenes,
  genesFromRegulatoryRegions
}
