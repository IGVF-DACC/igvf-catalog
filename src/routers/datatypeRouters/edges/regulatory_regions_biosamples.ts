import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { ontologyFormat } from '../nodes/ontologies'
import { regulatoryRegionFormat, regulatoryRegionsQueryFormat } from '../nodes/regulatory_regions'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'

const MAX_PAGE_SIZE = 50

// only have one type in this edge collection right now
const edgeTypes = z.object({
  type: z.enum([
    'MPRA_expression_tested'
  ]).optional()
})

function edgeQuery (input: paramsFormatType): string {
  let query = ''

  if (input.type !== undefined) {
    query = `record.type == '${input.type}'`
    delete input.type
  }

  return query
}

const regulatoryRegionToBiosampleFormat = z.object({
  'regulatory region': z.string().or(regulatoryRegionFormat).optional(),
  activity_score: z.number().nullable(),
  source: z.string().optional(),
  source_url: z.string().optional(),
  'biosample': z.string().or(z.array(ontologyFormat)).optional()
})

const schema = loadSchemaConfig()

const regulatoryRegionToBiosampleSchema = schema['regulatory element to biosample']
const regulatoryRegionSchema = schema['regulatory region']
const biosampleShema = schema['ontology term']

async function findRegulatoryRegionsFromBiosamplesQuery (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  if (input.term_id !== undefined) {
    input._id = `ontology_terms/${input.term_id}`
    delete input.term_id
  }

  let customFilter = edgeQuery(input)
  if (customFilter !== '') {
    customFilter = `and ${customFilter}`
  }

  let biosampleFilters = getFilterStatements(biosampleShema, input)
  if (biosampleFilters !== '') {
    biosampleFilters = `FILTER ${biosampleFilters}`
  }

  const verboseQuery = `
    FOR otherRecord IN ${regulatoryRegionSchema.db_collection_name}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(regulatoryRegionSchema).replaceAll('record', 'otherRecord')}}
  `

  const query = `
    LET targets = (
      FOR record IN ${biosampleShema.db_collection_name}
      ${biosampleFilters}
      RETURN record._id
    )

    FOR record IN ${regulatoryRegionToBiosampleSchema.db_collection_name}
      FILTER record._to IN targets ${customFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'regulatory region': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._from'},
        ${getDBReturnStatements(regulatoryRegionToBiosampleSchema)}
      }
  `

  return await (await db.query(query)).all()
}

async function findBiosamplesFromRegulatoryRegionsQuery (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let edgeFilter = edgeQuery(input)
  if (edgeFilter !== '') {
    edgeFilter = `and ${edgeFilter}`
  }

  let sourceFilters = getFilterStatements(regulatoryRegionSchema, preProcessRegionParam(input))
  if (sourceFilters !== '') {
    sourceFilters = `FILTER ${sourceFilters}`
  } else {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: `Region must be defined.`
    })
  }

  const verboseQuery = `
    FOR otherRecord IN ${biosampleShema.db_collection_name}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(biosampleShema).replaceAll('record', 'otherRecord')}}
  `

  const query = `
    LET sources = (
      FOR record in ${regulatoryRegionSchema.db_collection_name}
      ${sourceFilters}
      RETURN record._id
    )

    FOR record IN ${regulatoryRegionToBiosampleSchema.db_collection_name}
      FILTER record._from IN sources ${edgeFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'biosample': ${input.verbose === 'true' ? `(${verboseQuery})` : 'record._to'},
        ${getDBReturnStatements(regulatoryRegionToBiosampleSchema)}
      }
  `

  return await (await db.query(query)).all()
}

const regulatoryRegionsQuery = edgeTypes.merge(z.object({
  term_id: z.string().trim().optional(),
  term_name: z.string().trim().optional(),
  page: z.number().default(0),
  limit: z.number().optional(),
  verbose: z.enum(['true', 'false']).default('false')
})).transform(({term_name, ...rest}) => ({name: term_name, ...rest}))

const biosamplesFromRegulatoryRegions = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/regulatory_regions/biosamples', description: descriptions.regulatory_regions_biosamples } })
  .input(regulatoryRegionsQueryFormat.omit({ organism: true, biochemical_activity: true, source: true }).merge(edgeTypes).merge((z.object({ limit: z.number().optional(), verbose: z.enum(['true', 'false']).default('false') }))))
  .output(z.array(regulatoryRegionToBiosampleFormat))
  .query(async ({ input }) => await findBiosamplesFromRegulatoryRegionsQuery(input))

const regulatoryRegionsFromBiosamples = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/biosamples/regulatory_regions', description: descriptions.biosamples_regulatory_regions } })
  .input(regulatoryRegionsQuery)
  .output(z.array(regulatoryRegionToBiosampleFormat))
  .query(async ({ input }) => await findRegulatoryRegionsFromBiosamplesQuery(input))

export const regulatoryRegionsBiosamplesRouters = {
  biosamplesFromRegulatoryRegions,
  regulatoryRegionsFromBiosamples
}
