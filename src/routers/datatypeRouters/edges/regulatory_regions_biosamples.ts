import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { ontologyFormat } from '../nodes/ontologies'
import { regulatoryRegionFormat } from '../nodes/regulatory_regions'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonBiosamplesQueryFormat, commonHumanEdgeParamsFormat, regulatoryRegionsCommonQueryFormat } from '../params'

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
  activity_score: z.number().nullable(),
  source: z.string().optional(),
  source_url: z.string().optional(),
  regulatory_region: z.string().or(regulatoryRegionFormat).optional(),
  biosample: z.string().or(ontologyFormat).optional()
})

const schema = loadSchemaConfig()

const regulatoryRegionToBiosampleSchema = schema['regulatory element to biosample']
const regulatoryRegionSchema = schema['regulatory region']
const biosampleSchema = schema['ontology term']

const regulatoryRegionVerboseQuery = `
FOR otherRecord IN ${regulatoryRegionSchema.db_collection_name as string}
FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
RETURN {${getDBReturnStatements(regulatoryRegionSchema).replaceAll('record', 'otherRecord')}}
`
const biosampleVerboseQuery = `
FOR otherRecord IN ${biosampleSchema.db_collection_name as string}
FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
RETURN {${getDBReturnStatements(biosampleSchema).replaceAll('record', 'otherRecord')}}
`
async function findRegulatoryRegionsFromBiosamplesQuery (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  if (input.term_id !== undefined) {
    input._id = `ontology_terms/${input.term_id}`
    delete input.term_id
  }
  if (input.biosample_synonyms !== undefined) {
    input.synonyms = input.biosample_synonyms
    delete input.biosample_synonyms
  }

  let customFilter = edgeQuery(input)
  if (customFilter !== '') {
    customFilter = `and ${customFilter}`
  }

  let biosampleFilters = getFilterStatements(biosampleSchema, input)
  if (biosampleFilters !== '') {
    biosampleFilters = `FILTER ${biosampleFilters}`
  }

  const query = `
    LET targets = (
      FOR record IN ${biosampleSchema.db_collection_name as string}
      ${biosampleFilters}
      RETURN record._id
    )

    FOR record IN ${regulatoryRegionToBiosampleSchema.db_collection_name as string}
      FILTER record._to IN targets ${customFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'biosample': ${input.verbose === 'true' ? `(${biosampleVerboseQuery})[0]` : 'record._to'},
        'regulatory_region': ${input.verbose === 'true' ? `(${regulatoryRegionVerboseQuery})[0]` : 'record._from'},
        ${getDBReturnStatements(regulatoryRegionToBiosampleSchema)}
      }
  `
  return await (await db.query(query)).all()
}

async function findBiosamplesFromRegulatoryRegionsQuery (input: paramsFormatType): Promise<any[]> {
  delete input.organism
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
      message: 'Region must be defined.'
    })
  }

  const query = `
    LET sources = (
      FOR record in ${regulatoryRegionSchema.db_collection_name as string}
      ${sourceFilters}
      RETURN record._id
    )

    FOR record IN ${regulatoryRegionToBiosampleSchema.db_collection_name as string}
      FILTER record._from IN sources ${edgeFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'regulatory_region': ${input.verbose === 'true' ? `(${regulatoryRegionVerboseQuery})[0]` : 'record._from'},
        'biosample': ${input.verbose === 'true' ? `(${biosampleVerboseQuery})[0]` : 'record._to'},
        ${getDBReturnStatements(regulatoryRegionToBiosampleSchema)}
      }
  `
  return await (await db.query(query)).all()
}

const biosamplesFromRegulatoryRegions = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/regulatory-regions/biosamples', description: descriptions.regulatory_regions_biosamples } })
  .input(regulatoryRegionsCommonQueryFormat.omit({ biochemical_activity: true, source: true }).merge(edgeTypes).merge(commonHumanEdgeParamsFormat))
  .output(z.array(regulatoryRegionToBiosampleFormat))
  .query(async ({ input }) => await findBiosamplesFromRegulatoryRegionsQuery(input))

const regulatoryRegionsFromBiosamples = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/biosamples/regulatory-regions', description: descriptions.biosamples_regulatory_regions } })
  // eslint-disable-next-line @typescript-eslint/naming-convention
  .input(commonBiosamplesQueryFormat.merge(edgeTypes).merge(commonHumanEdgeParamsFormat).transform(({ biosample_name, biosample_id, ...rest }) => ({ name: biosample_name, term_id: biosample_id, ...rest })))
  .output(z.array(regulatoryRegionToBiosampleFormat))
  .query(async ({ input }) => await findRegulatoryRegionsFromBiosamplesQuery(input))

export const regulatoryRegionsBiosamplesRouters = {
  biosamplesFromRegulatoryRegions,
  regulatoryRegionsFromBiosamples
}
