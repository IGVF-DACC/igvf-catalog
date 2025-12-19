import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT, configType } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { distanceGeneVariant, getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { variantSearch, singleVariantQueryFormat, preProcessVariantParams, variantSimplifiedFormat } from '../nodes/variants'
import { commonHumanEdgeParamsFormat, genomicElementCommonQueryFormat, genomicElementType, variantsCommonQueryFormat } from '../params'
import { getSchema } from '../schema'
import { validateVariantInput } from './variants_genes'

const MAX_PAGE_SIZE = 300
const METHODS = ['caQTL', 'BlueSTARR', 'lentiMPRA'] as const
const SOURCES = ['IGVF', 'AFGR', 'ENCODE'] as const

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

const genomicElementsPredictionsFormat = z.object({
  'sequence variant': z.object({
    _id: z.string(),
    chr: z.string(),
    pos: z.number(),
    rsid: z.array(z.string()).nullable(),
    ref: z.string(),
    alt: z.string(),
    spdi: z.string().nullable(),
    hgvs: z.string().nullable(),
    ca_id: z.string().nullish()
  }),
  predictions: z.object({
    cell_types: z.array(z.string()),
    genes: z.array(z.object({
      gene_name: z.string().nullable(),
      id: z.string()
    }))
  })
})

const genomicElementsFromVariantsOutputFormat = z.array(z.object({
  variant: variantSimplifiedFormat,
  name: z.string(),
  label: z.string(),
  method: z.string(),
  class: z.string().nullish(),
  score: z.number().nullish(),
  files_filesets: z.string().nullish(),
  biosample_context: z.string().nullish(),
  biosample: z.object({
    _id: z.string(),
    name: z.string(),
    term_id: z.string(),
    uri: z.string()
  }).nullish(),
  genomic_element: z.object({
    _id: z.string(),
    name: z.string(),
    chr: z.string(),
    start: z.number(),
    end: z.number(),
    type: z.string(),
    source_annotation: z.string().nullish(),
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
    region_type: genomicElementType.optional(),
    method: z.enum(METHODS).optional(),
    files_fileset: z.string().optional(),
    source: z.enum(SOURCES).optional()
    // eslint-disable-next-line @typescript-eslint/naming-convention
  })).transform(({ region_type, ...rest }) => ({
    type: region_type,
    ...rest
  }))

const humanGeneCollectionName = 'genes' as string
const mouseGeneCollectionName = 'mm_genes' as string
const humanGenomicElementSchema = getSchema('data/schemas/nodes/genomic_elements.CCRE.json')
const mouseGenomicElementSchema = getSchema('data/schemas/nodes/mm_genomic_elements.HumanMouseElementAdapter.json')
const genomicElementToGeneCollectionName = 'genomic_elements_genes' as string
const humanVariantSchema = getSchema('data/schemas/nodes/variants.Favor.json')
const humanVariantCollectionName = humanVariantSchema.db_collection_name as string

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
  validateVariantInput(input)

  let genomicElementSchema = humanGenomicElementSchema
  let geneCollectionName = humanGeneCollectionName

  if (input.organism === 'Mus musculus') {
    genomicElementSchema = mouseGenomicElementSchema
    geneCollectionName = mouseGeneCollectionName
  }

  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = ` AND record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
    delete input.files_fileset
  }

  if (Object.keys(input).filter((key) => !['limit', 'page'].includes(key)).length === 1 && input.organism !== undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one node property for variant must be defined.'
    })
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
      FOR record IN ${genomicElementToGeneCollectionName}
      FILTER record._from IN ${`['${Object.keys(genomicElementsPerID).join('\',\'')}']`} ${filesetFilter}
      RETURN DISTINCT DOCUMENT(record.biological_context).name
    )

    LET geneIds = (
      FOR record IN ${genomicElementToGeneCollectionName}
      FILTER record._from IN ${`['${Object.keys(genomicElementsPerID).join('\',\'')}']`} ${filesetFilter}
      RETURN DISTINCT record._to
    )

    LET uniqueGenes = (
      FOR record IN ${geneCollectionName}
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
  validateVariantInput(input)

  let genomicElementSchema = humanGenomicElementSchema
  let geneCollectionName = humanGeneCollectionName

  if (input.organism === 'Mus musculus') {
    genomicElementSchema = mouseGenomicElementSchema
    geneCollectionName = mouseGeneCollectionName
  }
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

  if (Object.keys(input).filter((key) => !['limit', 'page'].includes(key)).length === 1 && input.organism !== undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one node property for variant must be defined.'
    })
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
    FOR otherRecord IN ${geneCollectionName}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN { gene_name: otherRecord.name, id: otherRecord._id, chr: otherRecord.chr, start: otherRecord.start, end: otherRecord.end }
  `

  const query = `
    FOR record IN ${genomicElementToGeneCollectionName}
    LET targetGene = (${geneVerboseQuery})[0]
    FILTER record._from IN ${`['${Object.keys(genomicElementsPerID).join('\',\'')}']`} and targetGene != NULL ${filesetFilter}
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

  let query = ''
  if (variantsFilters === '') {
    let filters = methodFilter.replace('AND', '')
    if (filters === '') {
      filters += filesetFilter.replace('AND', '')
    } else {
      filters += filesetFilter
    }

    if (filters === '') {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: 'At least one parameter must be defined.'
      })
    }

    query = `
      FOR record IN variants_genomic_elements
        FILTER ${filters}
        SORT record._key
        LIMIT ${page * limit}, ${limit}
        RETURN {
          'variant': (FOR variant in variants FILTER variant._id == record._from RETURN {${getDBReturnStatements(humanVariantSchema, true).replaceAll('record', 'variant')}})[0],
          'name': record.name,
          'label': record.label,
          'method': record.method,
          'class': record.class,
          'score': record.log2FC,
          'files_filesets': record.files_filesets,
          'biosample_context': record.biosample_context,
          'biosample': ( ${biosampleVerboseQuery} )[0],
          'genomic_element': ( ${genomicElementVerboseQuery} )[0]
        }
    `
  } else {
    query = `
      FOR variant IN ${humanVariantCollectionName}
      ${variantsFilters}
      FOR record IN variants_genomic_elements
        FILTER record._from == variant._id ${filesetFilter} ${methodFilter}
        SORT record._key
        LIMIT ${page * limit}, ${limit}
        RETURN {
          'variant': { ${getDBReturnStatements(humanVariantSchema, true).replaceAll('record', 'variant')} },
          'name': record.name,
          'label': record.label,
          'method': record.method,
          'class': record.class,
          'score': record.log2FC,
          'files_filesets': record.files_filesets,
          'biosample_context': record.biosample_context,
          'biosample': ( ${biosampleVerboseQuery} )[0],
          'genomic_element': ( ${genomicElementVerboseQuery} )[0]
        }
    `
  }

  console.log(query)
  return await (await db.query(query)).all()
}

async function findVariantsFromGenomicElementsQuery (input: paramsFormatType): Promise<any> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const page = input.page as number

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

  const sourceFilters = getFilterStatements(humanGenomicElementSchema, preProcessRegionParam(input))
  const empty = sourceFilters === ''

  if (empty) {
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

  const variantVerboseQuery = `
    FOR variant IN ${humanVariantCollectionName}
    FILTER variant._id == record._from
    RETURN { ${getDBReturnStatements(humanVariantSchema, true).replaceAll('record', 'variant')} }
  `

  const biosampleVerboseQuery = `
    FOR term IN ontology_terms
    FILTER term._id == record.biosample_term
    RETURN { _id: term._id, name: term.name, term_id: term.term_id, uri: term.uri }
  `

  const query = `
    ${empty
    ? ''
    : `
      FOR ge IN ${humanGenomicElementSchema.db_collection_name as string}
      FILTER ${sourceFilters.replaceAll('record', 'ge')}
    `}

      FOR record IN variants_genomic_elements
        FILTER ${empty ? '' : 'record._to == ge._id'} ${filesetFilter} ${methodFilter} ${sourceInputFilter}
        SORT record._key
        LIMIT ${page * limit}, ${limit}
        RETURN {
          'variant': ( ${variantVerboseQuery} )[0],
          'name': record.name,
          'label': record.label,
          'method': record.method,
          'class': record.class,
          'score': record.log2FC,
          'files_filesets': record.files_filesets,
          'biosample_context': record.biosample_context,
          'biosample': ( ${biosampleVerboseQuery} )[0],
          'genomic_element': DOCUMENT(record._to)
        }
  `

  return await (await db.query(query)).all()
}

async function findGenomicElementsPredictionsFromVariantsQuery (input: paramsFormatType): Promise<any> {
  let filterBy = ''
  const filterSts = getFilterStatements(humanVariantSchema, preProcessVariantParams(input))
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  } else {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one parameter must be defined.'
    })
  }

  const query = `
    FOR record IN variants
      ${filterBy}

      LET genomicElementIds = (
        FOR ge in genomic_elements
        FILTER ge.chr == record.chr and ge.start <= record.pos AND ge.end > record.pos
        RETURN ge._id
      )

      LET geneData = (
        FOR geneId IN genomic_elements_genes
          FILTER geneId._from IN genomicElementIds
          RETURN { geneId: geneId._to, cellTypeContext: geneId.biological_context }
      )

      LET geneIds = UNIQUE(geneData[*].geneId)
      LET cellTypeContexts = UNIQUE(geneData[*].cellTypeContext)

      LET cell_types = (
      FOR ctx IN cellTypeContexts
          FILTER ctx != NULL
          RETURN DISTINCT (CONTAINS(ctx, 'ontology_terms') ?  DOCUMENT(ctx).name : ctx )
      )

      LET genes = (
        FOR gene IN genes
        FILTER gene._id IN geneIds
        RETURN { gene_name: gene.name, id: gene._id }
      )

      RETURN {
        'sequence variant': {
          _id: record._key,
          chr: record.chr,
          pos: record.pos,
          rsid: record.rsid,
          ref: record.ref,
          alt: record.alt,
          spdi: record.spdi,
          hgvs: record.hgvs,
          ca_id: record.ca_id
        },
        predictions: { cell_types, genes }
      }
  `

  const obj = await (await db.query(query)).all()

  if (Array.isArray(obj) && obj.length === 0) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Variant not found.'
    })
  }

  return obj[0]
}

const genomicElementsFromVariantsCount = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/predictions-count', description: descriptions.variants_genomic_elements_count } })
  .input(singleVariantQueryFormat.merge(z.object({ files_fileset: z.string().optional() })))
  .output(z.any())
  .query(async ({ input }) => await findPredictionsFromVariantCount(input))

const predictionsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/predictions', description: descriptions.variants_genomic_elements } })
  .input(singleVariantQueryFormat.merge(z.object({ files_fileset: z.string().optional(), method: z.enum(METHODS).optional(), limit: z.number().optional(), page: z.number().default(0) })))
  .output(z.array(predictionFormat))
  .query(async ({ input }) => await findPredictionsFromVariant(input))

const genomicElementsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/genomic-elements', description: descriptions.variants_genomic_elements_edge } })
  .input(variantsCommonQueryFormat.merge(z.object({ region: z.string().optional(), method: z.enum(METHODS).optional(), files_fileset: z.string().optional() })).merge(commonHumanEdgeParamsFormat).omit({ organism: true, verbose: true, chr: true, position: true }))
  .output(genomicElementsFromVariantsOutputFormat)
  .query(async ({ input }) => await findGenomicElementsFromVariantsQuery(input))

const variantsFromGenomicElements = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genomic-elements/variants', description: descriptions.genomic_elements_variants_edge } })
  .input(genomicBiosamplesQuery)
  .output(genomicElementsFromVariantsOutputFormat)
  .query(async ({ input }) => await findVariantsFromGenomicElementsQuery(input))

const genomicElementsPredictionsFromVariant = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/genomic-elements/cell-gene-predictions', description: descriptions.cell_gene_genomic_elements } })
  .input(variantsCommonQueryFormat.omit({ chr: true, position: true }))
  .output(genomicElementsPredictionsFormat)
  .query(async ({ input }) => await findGenomicElementsPredictionsFromVariantsQuery(input))

export const variantsGenomicElementsRouters = {
  predictionsFromVariants,
  genomicElementsFromVariantsCount,
  genomicElementsPredictionsFromVariant,
  variantsFromGenomicElements,
  genomicElementsFromVariants
}
