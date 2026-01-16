import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { ontologyFormat } from '../nodes/ontologies'
import { genomicElementFormat } from '../nodes/genomic_elements'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonBiosamplesQueryFormat, commonHumanEdgeParamsFormat, genomicElementCommonQueryFormat } from '../params'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 50
const METHODS = ['MPRA', 'lentiMPRA'] as const
const SOURCES = ['ENCODE', 'IGVF'] as const

const genomicElementsToBiosampleFormat = z.object({
  activity_score: z.number().nullable(),
  source: z.string().optional(),
  source_url: z.string().optional(),
  genomic_element: z.string().or(genomicElementFormat).optional(),
  biosample: z.string().or(ontologyFormat).optional(),
  name: z.string(),
  class: z.string().optional(),
  method: z.string().optional()
})

const genomicElementToBiosampleSchema = getSchema('data/schemas/edges/genomic_elements_biosamples.EncodeMPRA.json')
const genomicElementToBiosampleCollectionName = genomicElementToBiosampleSchema.db_collection_name as string
const genomicElementSchema = getSchema('data/schemas/nodes/genomic_elements.CCRE.json')
const genomicElementCollectionName = genomicElementSchema.db_collection_name as string
const biosampleSchema = getSchema('data/schemas/nodes/ontology_terms.Ontology.json')
const biosampleCollectionName = biosampleSchema.db_collection_name as string

const genomicElementVerboseQuery = `
  FOR otherRecord IN ${genomicElementCollectionName}
  FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
  RETURN {${getDBReturnStatements(genomicElementSchema).replaceAll('record', 'otherRecord')}}
`
const biosampleVerboseQuery = `
  FOR otherRecord IN ${biosampleCollectionName}
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

  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = ` AND record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
    delete input.files_fileset
  }

  let methodFilter = ''
  if (input.method !== undefined) {
    methodFilter = ` AND record.method == '${input.method as string}'`
    delete input.method
  }

  let sourceInputFilter = ''
  if (input.source !== undefined) {
    sourceInputFilter = ` AND record.source == '${input.source as string}'`
    delete input.source
  }

  let biosampleFilters = getFilterStatements(biosampleSchema, input)
  const empty = biosampleFilters === ''
  if (!empty) {
    biosampleFilters = `FILTER ${biosampleFilters}`
  } else {
    if (filesetFilter !== '') {
      filesetFilter = filesetFilter.replace('AND', '')
    }

    if (methodFilter !== '' && filesetFilter === '') {
      methodFilter = methodFilter.replace('AND', '')
    }

    if (filesetFilter === '' && methodFilter === '' && sourceInputFilter !== '') {
      sourceInputFilter = sourceInputFilter.replace('AND', '')
    }

    if (filesetFilter === '' && methodFilter === '' && sourceInputFilter === '') {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: 'At least one parameter must be defined.'
      })
    }
  }

  const query = `
  ${empty
    ? ''
    : `
      LET targets = (
        FOR record IN ${biosampleCollectionName}
        ${biosampleFilters}
        RETURN record._id
      )
    `}

    FOR record IN ${genomicElementToBiosampleCollectionName}
      FILTER ${empty ? '' : 'record._to IN targets'} ${filesetFilter} ${methodFilter} ${sourceInputFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'biosample': ${input.verbose === 'true' ? `(${biosampleVerboseQuery})[0]` : 'record._to'},
        'genomic_element': ${input.verbose === 'true' ? `(${genomicElementVerboseQuery})[0]` : 'record._from'},
        ${getDBReturnStatements(genomicElementToBiosampleSchema)},
        'name': record.inverse_name,
        'class': record.class,
        'method': record.method
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

  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = ` AND record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
    delete input.files_fileset
  }

  let methodFilter = ''
  if (input.method !== undefined) {
    methodFilter = ` AND record.method == '${input.method as string}'`
    delete input.method
  }

  let sourceInputFilter = ''
  if (input.source !== undefined) {
    sourceInputFilter = ` AND record.source == '${input.source as string}'`
    delete input.source
  }

  let sourceFilters = getFilterStatements(genomicElementSchema, preProcessRegionParam(input))
  const empty = sourceFilters === ''
  if (!empty) {
    sourceFilters = `FILTER ${sourceFilters}`
  } else {
    if (filesetFilter !== '') {
      filesetFilter = filesetFilter.replace('AND', '')
    }

    if (methodFilter !== '' && filesetFilter === '') {
      methodFilter = methodFilter.replace('AND', '')
    }

    if (filesetFilter === '' && methodFilter === '' && sourceInputFilter !== '') {
      sourceInputFilter = sourceInputFilter.replace('AND', '')
    }

    if (filesetFilter === '' && methodFilter === '' && sourceInputFilter === '') {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: 'At least one parameter must be defined.'
      })
    }
  }

  const query = `
  ${empty
    ? ''
    : `
      LET sources = (
        FOR record in ${genomicElementCollectionName}
        ${sourceFilters}
        RETURN record._id
      )
    `}

    FOR record IN ${genomicElementToBiosampleCollectionName}
      FILTER ${empty ? '' : 'record._from IN sources'} ${filesetFilter} ${methodFilter} ${sourceInputFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'genomic_element': ${input.verbose === 'true' ? `(${genomicElementVerboseQuery})[0]` : 'record._from'},
        'biosample': ${input.verbose === 'true' ? `(${biosampleVerboseQuery})[0]` : 'record._to'},
        ${getDBReturnStatements(genomicElementToBiosampleSchema)},
        'name': record.name,
        'class': record.class,
        'method': record.method
      }
  `

  return await (await db.query(query)).all()
}

const genomicBiosamplesQuery = genomicElementCommonQueryFormat
  .merge(z.object({
    method: z.enum(METHODS).optional(),
    source: z.enum(SOURCES).optional(),
    files_fileset: z.string().optional()
  }))
  .merge(commonHumanEdgeParamsFormat).omit({
    source_annotation: true,
    organism: true
  // eslint-disable-next-line @typescript-eslint/naming-convention
  }).transform(({ region_type, ...rest }) => ({
    type: region_type,
    ...rest
  }))

const biosamplesGenomicElementsQuery = commonBiosamplesQueryFormat.merge(z.object({
  method: z.enum(METHODS).optional(),
  source: z.enum(SOURCES).optional(),
  files_fileset: z.string().optional()
// eslint-disable-next-line @typescript-eslint/naming-convention
})).merge(commonHumanEdgeParamsFormat).transform(({ biosample_name, ...rest }) => ({
  name: biosample_name, ...rest
}))

const biosamplesFromGenomicElements = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genomic-elements/biosamples', description: descriptions.genomic_elements_biosamples } })
  .input(genomicBiosamplesQuery)
  .output(z.array(genomicElementsToBiosampleFormat))
  .query(async ({ input }) => await findBiosamplesFromGenomicElementsQuery(input))

const genomicElementsFromBiosamples = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/biosamples/genomic-elements', description: descriptions.biosamples_genomic_elements } })
  .input(biosamplesGenomicElementsQuery)
  .output(z.array(genomicElementsToBiosampleFormat))
  .query(async ({ input }) => await findGenomicElementsFromBiosamplesQuery(input))

export const genomicElementsBiosamplesRouters = {
  biosamplesFromGenomicElements,
  genomicElementsFromBiosamples
}
