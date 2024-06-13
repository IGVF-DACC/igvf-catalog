import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT, configType } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { distanceGeneVariant, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { HS_ZKD_INDEX, MM_ZKD_INDEX } from '../nodes/regulatory_regions'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { singleVariantQueryFormat } from '../nodes/variants'

const MAX_PAGE_SIZE = 300

const schema = loadSchemaConfig()

const predictionFormat = z.object({
  'distance_gene_variant': z.number(),
  'enhancer_start': z.number(),
  'enhancer_end': z.number(),
  'enhancer_type': z.string(),
  'id': z.string(),
  'cell_type': z.string(),
  'target_gene': z.object({
    'gene_name': z.string(),
    'id': z.string(),
    'start': z.number(),
    'end': z.number()
  }),
  'score': z.number(),
  'model': z.string(),
  'dataset': z.string()
})

const humanGeneSchema = schema.gene
const mouseGeneSchema = schema['mouse gene']
const humanVariantSchema = schema['sequence variant']
const mouseVariantSchema = schema['sequence variant mouse']
const humanRegulatoryRegionSchema = schema['regulatory region']
const mouseRegulatoryRegionSchema = schema['regulatory region mouse']
const regulatoryRegionToGeneSchema = schema['regulatory element to gene expression association']

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
    RETURN { pos: record['pos:long'], region: CONCAT(record.chr, ':', record['pos:long'], '-', record['pos:long'])}
  `
  return await (await db.query(query)).all()
}

async function findInterceptingRegulatoryRegionsPerID (variant: paramsFormatType, zkdIndex: string, regulatoryRegionSchema: configType): Promise<any> {
  const useIndex = `OPTIONS { indexHint: "${zkdIndex}", forceIndexHint: true }`

  const variantInterval = preProcessRegionParam(variant)
  delete variantInterval.pos

  const query = `
    FOR record in ${regulatoryRegionSchema.db_collection_name} ${useIndex}
    FILTER ${getFilterStatements(regulatoryRegionSchema, variantInterval)}
    RETURN {'id': record._id, 'start': record['start:long'], 'end': record['end:long'], 'type': record.type}
  `

  const regulatoryRegions = await (await db.query(query)).all()

  const perID: Record<string, Record<string, string | number>> = {}
  regulatoryRegions.forEach(regulatoryRegion => {
    perID[regulatoryRegion.id] = {
      'enhancer_start': regulatoryRegion.start,
      'enhancer_end': regulatoryRegion.end,
      'enhancer_type': regulatoryRegion.type
    }
  })

  return perID
}

async function findPredictionsFromVariantCount (input: paramsFormatType): Promise<any> {
  let regulatoryRegionSchema = humanRegulatoryRegionSchema
  let zkdIndex = HS_ZKD_INDEX
  let geneSchema = humanGeneSchema

  if (input.organism === 'Mus musculus') {
    regulatoryRegionSchema = mouseRegulatoryRegionSchema
    zkdIndex = MM_ZKD_INDEX
    geneSchema = mouseGeneSchema
  }

  let variant = (await findVariant(input))

  if (variant.length === 0) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Variant not found.'
    })
  }

  const regulatoryRegionsPerID = await findInterceptingRegulatoryRegionsPerID(variant[0], zkdIndex, regulatoryRegionSchema)

  const query = `
    LET cellTypes = LENGTH(
      FOR record IN ${regulatoryRegionToGeneSchema.db_collection_name as string}
      FILTER record._from IN ${`[\'${Object.keys(regulatoryRegionsPerID).join('\',\'')}'\]`}
      RETURN DISTINCT record.biological_context
    )

    LET geneIds = (
      FOR record IN ${regulatoryRegionToGeneSchema.db_collection_name as string}
      FILTER record._from IN ${`[\'${Object.keys(regulatoryRegionsPerID).join('\',\'')}'\]`}
      RETURN DISTINCT record._to
    )

    LET uniqueGenes = (
      FOR record IN ${geneSchema.db_collection_name as string}
      FILTER record._id IN geneIds
      RETURN { gene_name: record.name, id: record._id }
    )

    RETURN {
      cell_types: cellTypes,
      genes: uniqueGenes
    }
  `

  console.log(query)
  return await (await db.query(query)).all()
}

async function findPredictionsFromVariant (input: paramsFormatType): Promise<any> {
  let regulatoryRegionSchema = humanRegulatoryRegionSchema
  let zkdIndex = HS_ZKD_INDEX
  let geneSchema = humanGeneSchema

  if (input.organism === 'Mus musculus') {
    regulatoryRegionSchema = mouseRegulatoryRegionSchema
    zkdIndex = MM_ZKD_INDEX
    geneSchema = mouseGeneSchema
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let variant = (await findVariant(input))

  if (variant.length === 0) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Variant not found.'
    })
  }

  const regulatoryRegionsPerID = await findInterceptingRegulatoryRegionsPerID(variant[0], zkdIndex, regulatoryRegionSchema)

  const geneVerboseQuery = `
    FOR otherRecord IN ${geneSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN { gene_name: otherRecord.name, id: otherRecord._id, start: otherRecord['start:long'], end: otherRecord['end:long'] }
  `

  const query = `
    FOR record IN ${regulatoryRegionToGeneSchema.db_collection_name as string}
    FILTER record._from IN ${`[\'${Object.keys(regulatoryRegionsPerID).join('\',\'')}'\]`}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN {
      'id': record._from,
      'cell_type': DOCUMENT(record.biological_context)['name'],
      'target_gene': (${geneVerboseQuery})[0],
      'score': record['score:long'],
      'model': record.source,
      'dataset': record.source_url
    }
  `

  const regulatoryRegionGenes = await (await db.query(query)).all()

  for (let i = 0; i < regulatoryRegionGenes.length; i++) {
    const distance = {'distance_gene_variant': distanceGeneVariant(regulatoryRegionGenes[i].target_gene.start, regulatoryRegionGenes[i].target_gene.end, variant[0].pos)}
    regulatoryRegionGenes[i] = {...distance, ...regulatoryRegionsPerID[regulatoryRegionGenes[i].id], ...regulatoryRegionGenes[i]}
  }

  return regulatoryRegionGenes
}

const regulatoryRegionsFromVariantsCount = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/predictions-count', description: descriptions.biosamples_regulatory_regions } })
  .input(singleVariantQueryFormat.omit({ page: true }))
  .output(z.any())
  .query(async ({ input }) => await findPredictionsFromVariantCount(input))

const regulatoryRegionsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/predictions', description: descriptions.biosamples_regulatory_regions } })
  .input(singleVariantQueryFormat.merge(z.object({ limit: z.number().optional() })))
  .output(z.array(predictionFormat))
  .query(async ({ input }) => await findPredictionsFromVariant(input))

export const variantsRegulatoryRegionsRouters = {
  regulatoryRegionsFromVariants,
  regulatoryRegionsFromVariantsCount
}
