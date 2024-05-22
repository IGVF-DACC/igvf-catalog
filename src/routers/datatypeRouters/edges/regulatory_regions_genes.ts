import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { geneFormat, genesQueryFormat } from '../nodes/genes'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { regulatoryRegionFormat, regulatoryRegionsQueryFormat } from '../nodes/regulatory_regions'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'

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

const regulatoryRegionToGeneFormat = z.object({
  score: z.number().nullable(),
  source: z.string().optional(),
  source_url: z.string().optional(),
  biological_context_name: z.string().nullable(),
  significant: z.boolean().optional(),
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

async function findRegulatoryRegionsFromGeneSearch (input: paramsFormatType): Promise<any[]> {
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

const genesQuery = genesQueryFormat.omit({
  organism: true,
  name: true
}).merge(z.object({
  gene_name: z.string().trim().optional(),
  limit: z.number().optional(),
  verbose: z.enum(['true', 'false']).default('false')
})).merge(edgeSources).transform(({ gene_name, ...rest }) => ({
  name: gene_name,
  ...rest
}))

const regulatoryRegionsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/regulatory_regions', description: descriptions.genes_regulatory_regions } })
  .input(genesQuery)
  .output(z.array(regulatoryRegionToGeneFormat))
  .query(async ({ input }) => await findRegulatoryRegionsFromGeneSearch(input))

const genesFromRegulatoryRegions = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/regulatory_regions/genes', description: descriptions.regulatory_regions_genes } })
  .input(regulatoryRegionsQueryFormat.omit({ organism: true }).merge(edgeSources).merge(z.object({ limit: z.number().optional(), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(regulatoryRegionToGeneFormat))
  .query(async ({ input }) => await findGenesFromRegulatoryRegionsSearch(input))

export const regulatoryRegionsGenesRouters = {
  regulatoryRegionsFromGenes,
  genesFromRegulatoryRegions
}
