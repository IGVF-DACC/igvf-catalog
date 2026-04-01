import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { QUERY_LIMIT } from '../../../constants'
import { db } from '../../../database'
import { TRPCError } from '@trpc/server'
import { variantFormat, variantIDSearch } from '../nodes/variants'
import { ontologyFormat, ontologySearch } from '../nodes/ontologies'
import { commonHumanEdgeParamsFormat, variantsCommonQueryFormat } from '../params'
import { getSchema, getCollectionEnumValuesOrThrow } from '../schema'

const MAX_PAGE_SIZE = 100

const METHODS = getCollectionEnumValuesOrThrow('edges', 'variants_biosamples', 'method')
const variantsBiosamplesQueryFormat = z.object({
  method: z.enum(METHODS).optional(),
  element_type: z.string().optional()
})
const biosamplesQueryFormat = z.object({
  biosample_id: z.string().trim().optional(),
  biosample_name: z.string().trim().optional(),
  files_fileset: z.string().optional()
}).merge(variantsBiosamplesQueryFormat).merge(commonHumanEdgeParamsFormat)

const genomicElementFormat = z.object({
  _id: z.string(),
  name: z.string().nullish(),
  chr: z.string().nullish(),
  start: z.number().nullish(),
  end: z.number().nullish(),
  type: z.string().nullish(),
  source: z.string().nullish(),
  source_url: z.string().nullish(),
  source_annotation: z.string().nullish()
})

const returnFormat = z.object({
  variant: z.string().or(variantFormat).optional(),
  biosample: z.string().or(ontologyFormat).optional(),
  genomic_element: z.string().or(genomicElementFormat).nullish(),
  log2FoldChange: z.number().nullish(),
  inputCountRef: z.number().nullish(),
  inputCountAlt: z.number().nullish(),
  outputCountRef: z.number().nullish(),
  outputCountAlt: z.number().nullish(),
  postProbEffect: z.number().nullish(),
  CI_lower_95: z.number().nullish(),
  CI_upper_95: z.number().nullish(),
  label: z.string(),
  method: z.string(),
  class: z.string().nullish(),
  source: z.string(),
  source_url: z.string(),
  name: z.string()
})

const variantToBiosamplesCollecionName = 'variants_biosamples'
const BiosampleSchema = getSchema('data/schemas/nodes/ontology_terms.Ontology.json')
const BiosampleCollectionName = BiosampleSchema.db_collection_name as string
const variantSchema = getSchema('data/schemas/nodes/variants.Favor.json')
const variantCollectionName = variantSchema.db_collection_name as string
const genomicElementsSchema = getSchema('data/schemas/nodes/genomic_elements.base.json')
const genomicElementsCollectionName = genomicElementsSchema.db_collection_name as string

function variantQueryValidation (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['variant_id', 'spdi', 'hgvs', 'rsid', 'region', 'ca_id', 'method', 'files_fileset'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one variant property must be defined.'
    })
  }
}

function biosampleQueryValidation (input: paramsFormatType): void {
  if (Object.keys(input).filter(item => !['biosample_id', 'biosample_name'].includes(item)).length === 0) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one biosample property must be defined.'
    })
  }
}

function getLimit (input: paramsFormatType): number {
  if (input.limit === undefined) {
    return QUERY_LIMIT
  } else {
    return (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
  }
}

const variantVerboseQuery = `
FOR otherRecord IN ${variantCollectionName}
FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
RETURN {${getDBReturnStatements(variantSchema).replaceAll('record', 'otherRecord')}}
`

const biosampleVerboseQuery = `
FOR otherRecord IN ${BiosampleCollectionName}
FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
RETURN {${getDBReturnStatements(BiosampleSchema).replaceAll('record', 'otherRecord')}}
`

const genomicElementVerboseQuery = `
FOR otherRecord IN ${genomicElementsCollectionName}
FILTER otherRecord._key == PARSE_IDENTIFIER(record.genomic_element).key
RETURN {${getDBReturnStatements(genomicElementsSchema).replaceAll('record', 'otherRecord')}}
`

async function executeVariantsBiosamplesQuery (input: paramsFormatType, variantIds: string[] | undefined, biosampleIds: string[] | undefined): Promise<any[]> {
  input.limit = getLimit(input)

  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = ` AND record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
    delete input.files_fileset
  }

  let methodFilter = input.method !== undefined ? `AND record.method == '${input.method as string}'` : ''

  let filterCondition = ''
  if (variantIds !== undefined) {
    if (variantIds.length === 0) {
      return []
    } else {
      filterCondition = `record._from IN ['${variantIds.join('\', \'')}']`
    }
  } else if (biosampleIds !== undefined) {
    if (biosampleIds.length === 0) {
      return []
    } else {
      filterCondition = `record._to IN ['${biosampleIds.join('\', \'')}']`
    }
  } else if (filesetFilter || methodFilter) {
    methodFilter = methodFilter.replace('AND', '')
    if (methodFilter.trim() === '') {
      filesetFilter = filesetFilter.replace('AND', '')
    }
  } else {
    return []
  }

  let filterGenomicElements = ''
  if (input.element_type !== undefined) {
    filterGenomicElements = `FILTER record.genomic_element == 'genomic_elements/${input.element_type as string}'`
    delete input.element_type
  }

  const query = `
    FOR record IN ${variantToBiosamplesCollecionName as string}
    FILTER ${filterCondition} ${methodFilter} ${filesetFilter}
    ${filterGenomicElements}
    LIMIT ${input.page as number * input.limit}, ${input.limit}
    RETURN {
      'variant': ${input.verbose === 'true' ? `(${variantVerboseQuery})[0]` : 'record._from'},
      'biosample': ${input.verbose === 'true' ? `(${biosampleVerboseQuery})[0]` : 'record._to'},
      'genomic_element': ${input.verbose === 'true' ? `(${genomicElementVerboseQuery})[0]` : 'record.genomic_element'},
      'log2FoldChange': record.log2FoldChange OR record.log2FC,
      'inputCountRef': record.inputCountRef,
      'inputCountAlt': record.inputCountAlt,
      'outputCountRef': record.outputCountRef,
      'outputCountAlt': record.outputCountAlt,
      'postProbEffect': record.postProbEffect,
      'CI_lower_95': record.CI_lower_95,
      'CI_upper_95': record.CI_upper_95,
      'label': record.label,
      'method': record.method,
      'class': record.class,
      'source': record.source,
      'source_url': record.source_url,
      'name': record.name
    }
  `

  return await ((await db.query(query)).all())
}

async function findVariantsFromBiosamplesSearch (input: paramsFormatType): Promise<any[]> {
  biosampleQueryValidation(input)
  delete input.organism
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const biosampleInput: paramsFormatType = (({ biosample_id, biosample_name }) => ({ term_id: biosample_id, name: biosample_name, page: 0 }))(input)
  delete input.biosample_id
  delete input.biosample_name

  let biosampleIds
  if (Object.values(biosampleInput).every(v => v === 0 || v === undefined)) {
    biosampleIds = undefined
  } else {
    const biosamples = await ontologySearch(biosampleInput)
    biosampleIds = biosamples.map(biosample => `ontology_terms/${biosample._id as string}`)
  }

  return await executeVariantsBiosamplesQuery(input, undefined, biosampleIds)
}

async function findBiosamplesFromVariantSearch (input: paramsFormatType): Promise<any[]> {
  variantQueryValidation(input)
  delete input.organism
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const variantInput: paramsFormatType = (({ variant_id, spdi, hgvs, rsid, region, ca_id }) => ({ variant_id, spdi, hgvs, rsid, region, ca_id }))(input)
  delete input.variant_id
  delete input.spdi
  delete input.hgvs
  delete input.rsid
  delete input.region
  delete input.ca_id

  let variantIDs
  if (Object.values(variantInput).every(v => v === undefined)) {
    variantIDs = undefined
  } else {
    variantIDs = await variantIDSearch(variantInput)
  }

  return await executeVariantsBiosamplesQuery(input, variantIDs, undefined)
}

const variantsFromBiosamples = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/biosamples/variants', description: descriptions.biosamples_variants } })
  .input(biosamplesQueryFormat)
  .output(z.array(returnFormat))
  .query(async ({ input }) => await findVariantsFromBiosamplesSearch(input))

const biosamplesFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/biosamples', description: descriptions.variants_biosamples } })
  .input(variantsCommonQueryFormat.merge(z.object({ files_fileset: z.string().optional() })).merge(variantsBiosamplesQueryFormat).merge(commonHumanEdgeParamsFormat))
  .output(z.array(returnFormat))
  .query(async ({ input }) => await findBiosamplesFromVariantSearch(input))

export const variantsBiosamplesRouters = {
  variantsFromBiosamples,
  biosamplesFromVariants
}
