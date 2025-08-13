import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT, configType } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { distanceGeneVariant, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { variantSearch, singleVariantQueryFormat } from '../nodes/variants'

const MAX_PAGE_SIZE = 300

const schema = loadSchemaConfig()

const predictionFormat = z.object({
  distance_gene_variant: z.number(),
  element_chr: z.string(),
  element_start: z.number(),
  element_end: z.number(),
  element_type: z.string(),
  id: z.string(),
  cell_type: z.string(),
  target_gene: z.object({
    gene_name: z.string(),
    id: z.string(),
    chr: z.string(),
    start: z.number(),
    end: z.number()
  }),
  score: z.number(),
  model: z.string(),
  dataset: z.string(),
  name: z.string()
})

const humanGeneSchema = schema.gene
const mouseGeneSchema = schema['mouse gene']
const humanGenomicElementSchema = schema['genomic element']
const mouseGenomicElementSchema = schema['genomic element mouse']
const genomicElementToGeneSchema = schema['genomic element to gene expression association']

async function findInterceptingGenomicElementsPerID (variant: paramsFormatType, genomicElementSchema: configType): Promise<any> {
  const variantInterval = preProcessRegionParam({
    pos: variant.pos,
    region: `${variant.chr as string}:${variant.pos as number}-${variant.pos as number + 1}`
  })
  delete variantInterval.pos

  const query = `
    FOR record in ${genomicElementSchema.db_collection_name as string}
    FILTER ${getFilterStatements(genomicElementSchema, variantInterval)}
    RETURN {'id': record._id, 'chr': record.chr, 'start': record.start, 'end': record.end, 'type': record.type}
  `

  const genomicElements = await (await db.query(query)).all()

  const perID: Record<string, Record<string, string | number>> = {}
  genomicElements.forEach(genomicElement => {
    perID[genomicElement.id] = {
      element_chr: genomicElement.chr,
      element_start: genomicElement.start,
      element_end: genomicElement.end,
      element_type: genomicElement.type
    }
  })

  return perID
}

export async function findPredictionsFromVariantCount (input: paramsFormatType, countGenes: boolean = true): Promise<any> {
  let genomicElementSchema = humanGenomicElementSchema
  let geneSchema = humanGeneSchema

  if (input.organism === 'Mus musculus') {
    genomicElementSchema = mouseGenomicElementSchema
    geneSchema = mouseGeneSchema
  }

  input.page = 0
  const variant = (await variantSearch(input))

  if (variant.length === 0) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Variant not found.'
    })
  }

  const genomicElementsPerID = await findInterceptingGenomicElementsPerID(variant[0], genomicElementSchema)

  let shouldCount = 'LENGTH'
  if (!countGenes) {
    shouldCount = ''
  }

  const query = `
    LET cellTypes = ${shouldCount}(
      FOR record IN ${genomicElementToGeneSchema.db_collection_name as string}
      FILTER record._from IN ${`['${Object.keys(genomicElementsPerID).join('\',\'')}']`}
      RETURN DISTINCT DOCUMENT(record.biological_context).name
    )

    LET geneIds = (
      FOR record IN ${genomicElementToGeneSchema.db_collection_name as string}
      FILTER record._from IN ${`['${Object.keys(genomicElementsPerID).join('\',\'')}']`}
      RETURN DISTINCT record._to
    )

    LET uniqueGenes = (
      FOR record IN ${geneSchema.db_collection_name as string}
      FILTER record._id IN geneIds
      RETURN { gene_name: record.name, id: record._id }
    )

    RETURN {
      cell_types: cellTypes,
      genes: uniqueGenes,
      name: 'regulates'
    }
  `
  return await (await db.query(query)).all()
}

async function findPredictionsFromVariant (input: paramsFormatType): Promise<any> {
  let genomicElementSchema = humanGenomicElementSchema
  let geneSchema = humanGeneSchema

  if (input.organism === 'Mus musculus') {
    genomicElementSchema = mouseGenomicElementSchema
    geneSchema = mouseGeneSchema
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const page = input.page as number

  input.page = 0
  const variant = (await variantSearch(input))

  if (variant.length === 0) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Variant not found.'
    })
  }

  const genomicElementsPerID = await findInterceptingGenomicElementsPerID(variant[0], genomicElementSchema)

  const geneVerboseQuery = `
    FOR otherRecord IN ${geneSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN { gene_name: otherRecord.name, id: otherRecord._id, chr: otherRecord.chr, start: otherRecord.start, end: otherRecord.end }
  `

  const query = `
    FOR record IN ${genomicElementToGeneSchema.db_collection_name as string}
    LET targetGene = (${geneVerboseQuery})[0]
    FILTER record._from IN ${`['${Object.keys(genomicElementsPerID).join('\',\'')}']`} and targetGene != NULL
    SORT record._key
    LIMIT ${page * limit}, ${limit}
    RETURN {
      'id': record._from,
      'cell_type': DOCUMENT(record.biological_context)['name'],
      'target_gene': targetGene,
      'score': record.score,
      'model': record.source,
      'dataset': record.source_url,
      'name': record.name
    }
  `

  const genomicElementGenes = await (await db.query(query)).all()

  for (let i = 0; i < genomicElementGenes.length; i++) {
    const distance = { distance_gene_variant: distanceGeneVariant(genomicElementGenes[i].target_gene.start, genomicElementGenes[i].target_gene.end, variant[0].pos) }
    genomicElementGenes[i] = { ...distance, ...genomicElementsPerID[genomicElementGenes[i].id], ...genomicElementGenes[i] }
  }
  return genomicElementGenes
}

const genomicElementsFromVariantsCount = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/predictions-count', description: descriptions.variants_genomic_elements_count } })
  .input(singleVariantQueryFormat)
  .output(z.any())
  .query(async ({ input }) => await findPredictionsFromVariantCount(input))

const genomicElementsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/predictions', description: descriptions.variants_genomic_elements } })
  .input(singleVariantQueryFormat.merge(z.object({ limit: z.number().optional(), page: z.number().default(0) })))
  .output(z.array(predictionFormat))
  .query(async ({ input }) => await findPredictionsFromVariant(input))

export const variantsGenomicElementsRouters = {
  genomicElementsFromVariants,
  genomicElementsFromVariantsCount
}
