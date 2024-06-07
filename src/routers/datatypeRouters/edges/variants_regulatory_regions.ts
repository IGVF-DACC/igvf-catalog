import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { ontologyFormat } from '../nodes/ontologies'
import { HS_ZKD_INDEX, MM_ZKD_INDEX, regulatoryRegionFormat, regulatoryRegionsQueryFormat } from '../nodes/regulatory_regions'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { singleVariantQueryFormat } from '../nodes/variants'

const MAX_PAGE_SIZE = 50


const schema = loadSchemaConfig()

const humanGeneSchema = schema.gene
const mouseGeneSchema = schema['mouse gene']
const humanVariantSchema = schema['sequence variant']
const mouseVariantSchema = schema['sequence variant mouse']
const humanRegulatoryRegionSchema = schema['regulatory region']
const mouseRegulatoryRegionSchema = schema['regulatory region mouse']
const regulatoryRegionToGeneSchema = schema['regulatory element to gene expression association']

async function findPredictionsFromVariant (input: paramsFormatType): Promise<any[]> {
  const regulatoryRegions = await findRegulatoryRegions(input)

  return regulatoryRegions
}

async function findRegulatoryRegions (input: paramsFormatType): Promise<any[]> {
  let regulatoryRegionSchema = humanRegulatoryRegionSchema
  let zkd_index = HS_ZKD_INDEX
  let geneSchema = humanGeneSchema
  if (input.organism === 'Mus musculus') {
    regulatoryRegionSchema = mouseRegulatoryRegionSchema
    zkd_index = MM_ZKD_INDEX
    geneSchema = mouseGeneSchema
  }

  let variant = (await findVariant(input))

  if (variant.length === 0) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Variant not found.'
    })
  }

  variant = variant[0]

  const useIndex = `OPTIONS { indexHint: "${zkd_index}", forceIndexHint: true }`

  const geneVerboseQuery = `
    FOR otherRecord IN ${geneSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(geneSchema).replaceAll('record', 'otherRecord')}}`

  const query = `
    LET regulatoryRegions = (
      FOR record in ${regulatoryRegionSchema.db_collection_name} ${useIndex}
      FILTER ${getFilterStatements(regulatoryRegionSchema, preProcessRegionParam(variant))}
      RETURN record._id
    )

    FOR record IN ${regulatoryRegionToGeneSchema.db_collection_name as string}
    FILTER record._from IN regulatoryRegions
    RETURN {
      ${getDBReturnStatements(regulatoryRegionToGeneSchema)},
      'biological_context_name': DOCUMENT(record.biological_context)['name'],
      'gene': (${geneVerboseQuery})[0]
    }
  `

  return await (await db.query(query)).all()
}

async function findVariant (input: paramsFormatType): Promise<any[]> {
  let variantSchema = humanVariantSchema
  if (input.organism === 'Mus musculus') {
    variantSchema = mouseVariantSchema
  }
  delete input.organism

  if (input.variant_id !== undefined) {
    input._key = input.variant_id
    delete input.variant_id
  }

  let filterBy = ''
  const filterSts = getFilterStatements(variantSchema, input)
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  } else {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one property must be defined.'
    })
  }

  const query = `
    FOR record IN ${variantSchema.db_collection_name as string}
    ${filterBy}
    RETURN { region: CONCAT(record.chr, ':', record['pos:long'], '-', record['pos:long'])}
  `
  return await (await db.query(query)).all()
}

const regulatoryRegionsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/predictions', description: descriptions.biosamples_regulatory_regions } })
  .input(singleVariantQueryFormat)
  .output(z.any())
  .query(async ({ input }) => await findPredictionsFromVariant(input))

export const variantsRegulatoryRegionsRouters = {
  regulatoryRegionsFromVariants
}
