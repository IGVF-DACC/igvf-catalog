import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { ontologyFormat } from '../nodes/ontologies'
import { genomicElementFormat } from '../nodes/genomic_elements'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonBiosamplesQueryFormat, commonHumanEdgeParamsFormat, genomicElementCommonQueryFormat } from '../params'

const MAX_PAGE_SIZE = 50

const genomicElementsToBiosampleFormat = z.object({
  activity_score: z.number().nullable(),
  source: z.string().optional(),
  source_url: z.string().optional(),
  genomic_element: z.string().or(genomicElementFormat).optional(),
  biosample: z.string().or(ontologyFormat).optional(),
  name: z.string()
})

const schema = loadSchemaConfig()

const genomicElementToBiosampleSchema = schema['genomic element to biosample']
const genomicElementSchema = schema['genomic element']
const biosampleSchema = schema['ontology term']

const genomicElementVerboseQuery = `
  FOR otherRecord IN ${genomicElementSchema.db_collection_name as string}
  FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
  RETURN {${getDBReturnStatements(genomicElementSchema).replaceAll('record', 'otherRecord')}}
`
const biosampleVerboseQuery = `
  FOR otherRecord IN ${biosampleSchema.db_collection_name as string}
  FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
  RETURN {${getDBReturnStatements(biosampleSchema).replaceAll('record', 'otherRecord')}}
`
async function findGenomicElementsFromBiosamplesQuery (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  if (input.term_id !== undefined) {
    input._id = `ontology_terms/${input.term_id as string}`
    delete input.term_id
  }
  if (input.biosample_synonyms !== undefined) {
    input.synonyms = input.biosample_synonyms
    delete input.biosample_synonyms
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

    FOR record IN ${genomicElementToBiosampleSchema.db_collection_name as string}
      FILTER record._to IN targets
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'biosample': ${input.verbose === 'true' ? `(${biosampleVerboseQuery})[0]` : 'record._to'},
        'genomic_element': ${input.verbose === 'true' ? `(${genomicElementVerboseQuery})[0]` : 'record._from'},
        ${getDBReturnStatements(genomicElementToBiosampleSchema)},
        'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
      }
  `
  return await (await db.query(query)).all()
}

async function findBiosamplesFromGenomicElementsQuery (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let sourceFilters = getFilterStatements(genomicElementSchema, preProcessRegionParam(input))
  if (sourceFilters !== '') {
    sourceFilters = `FILTER ${sourceFilters}`
  } else {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'At least one parameter must be defined.'
    })
  }

  const query = `
    LET sources = (
      FOR record in ${genomicElementSchema.db_collection_name as string}
      ${sourceFilters}
      RETURN record._id
    )

    FOR record IN ${genomicElementToBiosampleSchema.db_collection_name as string}
      FILTER record._from IN sources
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'genomic_element': ${input.verbose === 'true' ? `(${genomicElementVerboseQuery})[0]` : 'record._from'},
        'biosample': ${input.verbose === 'true' ? `(${biosampleVerboseQuery})[0]` : 'record._to'},
        ${getDBReturnStatements(genomicElementToBiosampleSchema)},
        'name': record.name
      }
  `

  return await (await db.query(query)).all()
}

const genomicBiosamplesQuery = genomicElementCommonQueryFormat.omit({
  source_annotation: true,
  source: true
// eslint-disable-next-line @typescript-eslint/naming-convention
}).transform(({ region_type, ...rest }) => ({
  type: region_type,
  ...rest
}))

const biosamplesFromGenomicElements = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genomic-elements/biosamples', description: descriptions.genomic_elements_biosamples } })
  .input(genomicBiosamplesQuery)
  .output(z.array(genomicElementsToBiosampleFormat))
  .query(async ({ input }) => await findBiosamplesFromGenomicElementsQuery(input))

const genomicElementsFromBiosamples = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/biosamples/genomic-elements', description: descriptions.biosamples_genomic_elements } })
  // eslint-disable-next-line @typescript-eslint/naming-convention
  .input(commonBiosamplesQueryFormat.merge(commonHumanEdgeParamsFormat).transform(({ biosample_name, biosample_id, ...rest }) => ({ name: biosample_name, term_id: biosample_id, ...rest })))
  .output(z.array(genomicElementsToBiosampleFormat))
  .query(async ({ input }) => await findGenomicElementsFromBiosamplesQuery(input))

export const genomicElementsBiosamplesRouters = {
  biosamplesFromGenomicElements,
  genomicElementsFromBiosamples
}
