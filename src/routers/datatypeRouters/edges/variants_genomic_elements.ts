import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT, configType } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { distanceGeneVariant, getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { variantSearch, singleVariantQueryFormat, preProcessVariantParams, variantSimplifiedFormat } from '../nodes/variants'
import { commonHumanEdgeParamsFormat, genomicElementCommonQueryFormat, genomicElementType, variantsCommonQueryFormat } from '../params'

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

const genomicElementsFromVariantsOutputFormat = z.array(z.object({
  variant: variantSimplifiedFormat,
  name: z.string(),
  label: z.string(),
  method: z.string(),
  score: z.number().nullish(),
  biosample_context: z.string().nullish(),
  biosample: z.object({
    _id: z.string(),
    name: z.string(),
    term_id: z.string(),
    uri: z.string()
  }).nullish(),
  genomic_element: z.object({
    _id: z.string(),
    chr: z.string(),
    start: z.number(),
    end: z.number(),
    type: z.string(),
    source_annotation: z.string(),
    source: z.string(),
    source_url: z.string()
  }).nullish()
}))

const genomicBiosamplesQuery = genomicElementCommonQueryFormat
  .merge(commonHumanEdgeParamsFormat)
  .omit({
    source_annotation: true,
    source: true,
    organism: true,
    verbose: true
  }).merge(z.object({
    region_type: genomicElementType.optional()
    // eslint-disable-next-line @typescript-eslint/naming-convention
  })).transform(({ region_type, ...rest }) => ({
    type: region_type,
    ...rest
  }))

const humanGeneSchema = schema.gene
const mouseGeneSchema = schema['mouse gene']
const humanGenomicElementSchema = schema['genomic element']
const mouseGenomicElementSchema = schema['genomic element mouse']
const genomicElementToGeneSchema = schema['genomic element to gene expression association']
const humanVariantSchema = schema['sequence variant']

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

async function findGenomicElementsFromVariantsQuery (input: paramsFormatType): Promise<any> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const page = input.page as number

  let variantsFilters = ''
  const filterSts = getFilterStatements(humanVariantSchema, preProcessVariantParams(input))
  if (filterSts !== '') {
    variantsFilters = `FILTER ${filterSts.replaceAll('record', 'variant')}`
  }

  const biosampleVerboseQuery = `
    FOR term IN ontology_terms
    FILTER term._id == record.biosample_term
    RETURN { _id: term._id, name: term.name, term_id: term.term_id, uri: term.uri }
  `

  const genomicElementVerboseQuery = `
    FOR element IN ${humanGenomicElementSchema.db_collection_name as string}
    FILTER element._id == record._to
    RETURN { ${getDBReturnStatements(humanGenomicElementSchema).replaceAll('record', 'element')} }
  `

  const query = `
    FOR variant IN ${humanVariantSchema.db_collection_name as string}
    ${variantsFilters}
    FOR record IN variants_genomic_elements
      FILTER record._from == variant._id
      SORT record._key
      LIMIT ${page * limit}, ${limit}
      RETURN {
        'variant': { ${getDBReturnStatements(humanVariantSchema, true).replaceAll('record', 'variant')} },
        'name': record.name,
        'label': record.label,
        'method': record.method,
        'score': record.log2FC,
        'biosample_context': record.biosample_context,
        'biosample': ( ${biosampleVerboseQuery} )[0],
        'genomic_element': ( ${genomicElementVerboseQuery} )[0]
      }
  `

  return await (await db.query(query)).all()
}

async function findVariantsFromGenomicElementsQuery (input: paramsFormatType): Promise<any> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const page = input.page as number

  let sourceFilters = getFilterStatements(humanGenomicElementSchema, preProcessRegionParam(input))
  if (sourceFilters !== '') {
    sourceFilters = `FILTER ${sourceFilters.replaceAll('record', 'ge')}`
  } else {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'At least one parameter must be defined.'
    })
  }

  const variantVerboseQuery = `
    FOR variant IN ${humanVariantSchema.db_collection_name as string}
    FILTER variant._id == record._from
    RETURN { ${getDBReturnStatements(humanVariantSchema, true).replaceAll('record', 'variant')} }
  `

  const biosampleVerboseQuery = `
    FOR term IN ontology_terms
    FILTER term._id == record.biosample_term
    RETURN { _id: term._id, name: term.name, term_id: term.term_id, uri: term.uri }
  `

  const query = `
    FOR ge IN ${humanGenomicElementSchema.db_collection_name as string}
    ${sourceFilters}
    FOR record IN variants_genomic_elements
      FILTER record._to == ge._id
      SORT record._key
      LIMIT ${page * limit}, ${limit}
      RETURN {
        'variant': ( ${variantVerboseQuery} )[0],
        'name': record.name,
        'label': record.label,
        'method': record.method,
        'score': record.log2FC,
        'biosample_context': record.biosample_context,
        'biosample': ( ${biosampleVerboseQuery} )[0],
        'genomic_element': { ${getDBReturnStatements(humanGenomicElementSchema).replaceAll('record', 'ge')} }
      }
  `

  return await (await db.query(query)).all()
}

const genomicElementsFromVariantsCount = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/predictions-count', description: descriptions.variants_genomic_elements_count } })
  .input(singleVariantQueryFormat)
  .output(z.any())
  .query(async ({ input }) => await findPredictionsFromVariantCount(input))

const predictionsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/predictions', description: descriptions.variants_genomic_elements } })
  .input(singleVariantQueryFormat.merge(z.object({ limit: z.number().optional(), page: z.number().default(0) })))
  .output(z.array(predictionFormat))
  .query(async ({ input }) => await findPredictionsFromVariant(input))

const genomicElementsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/genomic-elements', description: descriptions.variants_genomic_elements_edge } })
  .input(variantsCommonQueryFormat.merge(z.object({ region: z.string().optional() })).merge(commonHumanEdgeParamsFormat).omit({ organism: true, verbose: true, chr: true, position: true }))
  .output(genomicElementsFromVariantsOutputFormat)
  .query(async ({ input }) => await findGenomicElementsFromVariantsQuery(input))

const variantsFromGenomicElements = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genomic-elements/variants', description: descriptions.genomic_elements_variants_edge } })
  .input(genomicBiosamplesQuery)
  .output(genomicElementsFromVariantsOutputFormat)
  .query(async ({ input }) => await findVariantsFromGenomicElementsQuery(input))

export const variantsGenomicElementsRouters = {
  predictionsFromVariants,
  genomicElementsFromVariantsCount,
  variantsFromGenomicElements,
  genomicElementsFromVariants
}
