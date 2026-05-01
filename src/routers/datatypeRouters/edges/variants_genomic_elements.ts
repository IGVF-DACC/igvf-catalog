import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT, configType } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { variantSearch, singleVariantQueryFormat, preProcessVariantParams, variantSimplifiedFormat, variantIDSearch } from '../nodes/variants'
import { commonHumanEdgeParamsFormat, genomicElementCommonQueryFormat, variantsCommonQueryFormat } from '../params'
import { getCollectionEnumValuesOrThrow, getSchema } from '../schema'
import { validateVariantInput } from './variants_genes'

const MAX_PAGE_SIZE = 300

const METHODS = getCollectionEnumValuesOrThrow('edges', 'variants_genomic_elements', 'method')
const SOURCES = getCollectionEnumValuesOrThrow('edges', 'variants_genomic_elements', 'source')
// need to drop candidate cis regulatory element and tested elements for this endpoint
const GENOMIC_ELEMENT_TYPES = getCollectionEnumValuesOrThrow('nodes', 'genomic_elements', 'type').filter(type => type !== 'candidate cis regulatory element' && type !== 'tested elements') as [string, ...string[]]
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
  name: z.string(),
  files_filesets: z.string().nullish()
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
  log2FC: z.number().nullish(),
  nlog10pval: z.number().nullish(),
  beta: z.number().nullish(),
  files_filesets: z.string().nullish(),
  biological_context: z.string().nullish(),
  biosample_term: z.string().nullish(),
  source: z.string().nullish(),
  source_url: z.string().nullish(),
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
  .merge(z.object({
    region_type: z.enum(GENOMIC_ELEMENT_TYPES).optional(),
    biosample_term: z.string().optional(),
    biological_context: z.string().optional(),
    method: z.enum(METHODS).optional(),
    files_fileset: z.string().optional(),
    source: z.enum(SOURCES).optional()
  })).merge(commonHumanEdgeParamsFormat)
  .omit({
    source_annotation: true,
    source: true,
    organism: true,
    verbose: true
  // eslint-disable-next-line @typescript-eslint/naming-convention
  }).transform(({ region_type, ...rest }) => ({
    type: region_type,
    ...rest
  }))

const variantsQueryFormat = variantsCommonQueryFormat
  .merge(z.object({
    region: z.string().optional(),
    biosample_term: z.string().optional(),
    biological_context: z.string().optional(),
    method: z.enum(METHODS).optional(),
    files_fileset: z.string().optional()
  }))
  .merge(commonHumanEdgeParamsFormat)
  .omit({ organism: true, verbose: true })

const regionSummaryFormat = z.object({
  variant_count: z.number(),
  by_method: z.array(z.object({
    method: z.string(),
    count: z.number()
  }))
})

const humanGeneCollectionName = 'genes' as string
const mouseGeneCollectionName = 'mm_genes' as string
const humanGenomicElementSchema = getSchema('data/schemas/nodes/genomic_elements.CCRE.json')
const mouseGenomicElementSchema = getSchema('data/schemas/nodes/mm_genomic_elements.HumanMouseElementAdapter.json')
const genomicElementToGeneCollectionName = 'genomic_elements_genes' as string
const humanVariantSchema = getSchema('data/schemas/nodes/variants.Favor.json')
const mouseVariantSchema = getSchema('data/schemas/nodes/mm_variants.MouseGenomesProjectAdapter.json')
const variantsGenomicElementsAFGRCAQtl = getSchema('data/schemas/edges/variants_genomic_elements.AFGRCAQtl.json')

function validateVariantPredictionsInput (input: paramsFormatType): void {
  const isInvalidInput = Object.keys(input).every(item => !['spdi', 'hgvs', 'rsid', 'ca_id', 'variant_id'].includes(item))
  if (isInvalidInput) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one of these properties must be defined: spdi, hgvs, rsid, ca_id, variant_id'
    })
  }
}

function variantQueryValidation (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['spdi', 'hgvs', 'rsid', 'ca_id', 'variant_id', 'region', 'method', 'files_fileset'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one variant property or method or files_fileset must be defined.'
    })
  }
}

function genomicElementQueryValidation (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['region', 'method', 'files_fileset'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one of these properties must be defined: region, method, files_fileset.'
    })
  }
}

const getQueryLimit = (input: paramsFormatType): number => {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  return limit
}

const getEdgeFilters = (input: paramsFormatType): string => {
  if (input.files_fileset !== undefined) {
    input.files_filesets = `files_filesets/${input.files_fileset as string}`
    delete input.files_fileset
  }
  if (input.biosample_term !== undefined) {
    input.biosample_term = `ontology_terms/${input.biosample_term as string}`
  }
  return getFilterStatements(variantsGenomicElementsAFGRCAQtl, input)
}

const buildReturnObject = (): string => `{
  'variant': (FOR variant IN variants FILTER variant._id == record._from LIMIT 1 RETURN {${getDBReturnStatements(humanVariantSchema, true).replaceAll('record', 'variant')}})[0],
  'name': record.name,
  'label': record.label,
  'method': record.method,
  'class': record.class,
  'log2FC': record.log2FC,
  'nlog10pval': record.log10pvalue,
  'beta': record.beta,
  'files_filesets': record.files_filesets,
  'biological_context': record.biological_context,
  'biosample_term': record.biosample_term,
  'source': record.source,
  'source_url': record.source_url,
  'genomic_element': (FOR element IN genomic_elements FILTER element._id == record._to LIMIT 1 RETURN { ${getDBReturnStatements(humanGenomicElementSchema).replaceAll('record', 'element')} })[0]
}`

const executeQuery = async (query: string, bindVars?: Record<string, unknown>): Promise<any[]> => {
  const cursor = bindVars ? await db.query(query, bindVars) : await db.query(query)
  return await cursor.all()
}

const executeExactMatchQuery = async ({
  biologicalContext,
  filterStatement,
  limit,
  page,
  bindVars
}: {
  biologicalContext: string | undefined
  filterStatement: string
  limit: number
  page: number
  bindVars?: Record<string, unknown>
}): Promise<any[]> => {
  const offset = page * limit
  const biologicalContextFilter = biologicalContext
    ? ` AND record.biological_context == "${biologicalContext.replace(/"/g, '\\"')}"`
    : ''
  const query = `
    FOR record IN variants_genomic_elements
      ${filterStatement}${biologicalContextFilter}
      SORT record._key
      LIMIT ${offset}, ${limit}
      RETURN ${buildReturnObject()}
  `
  return await executeQuery(query, bindVars)
}

const executePrefixMatchQuery = async ({
  biologicalContext,
  filterStatement,
  limit,
  page,
  searchViewName,
  bindVars
}: {
  biologicalContext: string
  filterStatement: string
  limit: number
  page: number
  searchViewName: string
  bindVars?: Record<string, unknown>
}): Promise<any[]> => {
  const offset = page * limit
  const searchVal = biologicalContext.replace(/"/g, '\\"')
  const query = `
    FOR record IN ${searchViewName}
      SEARCH STARTS_WITH(record.biological_context, "${searchVal}")
      ${filterStatement}
      SORT record._key
      LIMIT ${offset}, ${limit}
      RETURN ${buildReturnObject()}
  `
  return await executeQuery(query, bindVars)
}

const executeTokenMatchQuery = async ({
  biologicalContext,
  filterStatement,
  limit,
  page,
  searchViewName,
  bindVars
}: {
  biologicalContext: string
  filterStatement: string
  limit: number
  page: number
  searchViewName: string
  bindVars?: Record<string, unknown>
}): Promise<any[]> => {
  const offset = page * limit
  const searchVal = biologicalContext.replace(/"/g, '\\"')
  const query = `
    FOR record IN ${searchViewName}
      SEARCH ANALYZER(TOKENS("${searchVal}", "text_en_no_stem") ALL IN record.biological_context, "text_en_no_stem")
      ${filterStatement}
      SORT record._key
      LIMIT ${offset}, ${limit}
      RETURN ${buildReturnObject()}
  `
  return await executeQuery(query, bindVars)
}

const executeLevenshteinMatchQuery = async ({
  biologicalContext,
  filterStatement,
  limit,
  page,
  searchViewName,
  bindVars
}: {
  biologicalContext: string
  filterStatement: string
  limit: number
  page: number
  searchViewName: string
  bindVars?: Record<string, unknown>
}): Promise<any[]> => {
  const offset = page * limit
  const searchVal = biologicalContext.replace(/"/g, '\\"')
  const query = `
    FOR record IN ${searchViewName}
      SEARCH LEVENSHTEIN_MATCH(record.biological_context, "${searchVal}", 1, false)
      ${filterStatement}
      SORT record._key
      LIMIT ${offset}, ${limit}
      RETURN ${buildReturnObject()}
  `
  return await executeQuery(query, bindVars)
}

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
      RETURN DISTINCT record.biological_context
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

async function findVariantsRegionSummary (input: paramsFormatType): Promise<any> {
  if (input.region === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Region parameter is required.'
    })
  }

  const processedInput = preProcessVariantParams({ region: input.region })
  const coordinates = (processedInput.pos as string).split(':')[1].split('-').map(Number)

  if (coordinates[1] - coordinates[0] > 10000) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Region length cannot exceed 10kb.'
    })
  }

  const query = `
    LET variant_keys = (
      FOR v IN variants
        FILTER ${getFilterStatements(humanVariantSchema, processedInput).replaceAll('record', 'v')}
        RETURN v._id
    )

    LET all_methods = (
      FOR variant IN variant_keys
        FOR coll IN [
          (FOR r IN variants_genes            FILTER r._from == variant RETURN r.method),
          (FOR r IN variants_proteins         FILTER r._from == variant RETURN r.method),
          (FOR r IN variants_biosamples       FILTER r._from == variant RETURN r.method),
          (FOR r IN variants_genomic_elements FILTER r._from == variant RETURN r.method),
          (FOR r IN variants_phenotypes       FILTER r._from == variant RETURN r.method)
        ]
        FOR method IN coll
          RETURN method
    )

    LET method_counts = (
      FOR method IN all_methods
        COLLECT m = method WITH COUNT INTO count
        RETURN { method: m, count: count }
    )

    RETURN {
      variant_count: LENGTH(variant_keys),
      by_method: method_counts
    }
  `

  const obj = await (await db.query(query)).all()
  if (Array.isArray(obj) && obj.length > 0) {
    return obj[0]
  }
  return obj
}

async function findPredictionsFromVariant (input: paramsFormatType): Promise<any> {
  validateVariantPredictionsInput(input)

  let genomicElementSchema = humanGenomicElementSchema
  let geneCollectionName = humanGeneCollectionName
  let variantSchema = humanVariantSchema

  if (input.organism === 'Mus musculus') {
    genomicElementSchema = mouseGenomicElementSchema
    geneCollectionName = mouseGeneCollectionName
    variantSchema = mouseVariantSchema
  }
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

  const page = input.page as number

  input.page = 0 // for variants query

  const geneVerboseQuery = `
    FOR otherRecord IN ${geneCollectionName}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN { gene_name: otherRecord.name, id: otherRecord._id, chr: otherRecord.chr, start: otherRecord.start, end: otherRecord.end }
  `

  const query = `
    FOR variant IN ${variantSchema.db_collection_name as string}
    FILTER ${getFilterStatements(variantSchema, preProcessVariantParams(input)).replaceAll('record', 'variant')}

      FOR ge IN ${genomicElementSchema.db_collection_name as string}
      FILTER ge.chr == variant.chr and ge.start <= variant.pos AND ge.end >= variant.pos

        FOR record IN ${genomicElementToGeneCollectionName}
          FILTER record._from == ge._id ${filesetFilter}
          LET targetGene = (${geneVerboseQuery})[0]
          FILTER targetGene != NULL
          SORT record._key
          LIMIT ${page * limit}, ${limit}

          LET distToStart = ABS(variant.pos - targetGene.start)
          LET distToEnd   = ABS(variant.pos - targetGene.end)

          RETURN {
            'id': record._from,
            'cell_type': record.biological_context,
            'target_gene': targetGene,
            'score': record.score,
            'model': record.source,
            'dataset': record.source_url,
            'name': record.name,
            'distance_gene_variant': MIN([distToStart, distToEnd]),
            'element_chr': ge.chr,
            'element_start': ge.start,
            'element_end': ge.end,
            'element_type': ge.type,
            'files_filesets': record.files_filesets
          }
  `

  return await (await db.query(query)).all()
}

async function findGenomicElementsFromVariantsQuery (input: paramsFormatType): Promise<any> {
  variantQueryValidation(input)
  const limit = getQueryLimit(input)
  const page = input.page as number
  const biologicalContext = input.biological_context
  delete input.biological_context

  let variantIDs: string[] = []
  const isVariantQuery = Object.keys(input).some(item => ['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id', 'region'].includes(item))
  if (isVariantQuery) {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const variantInput: paramsFormatType = (({ variant_id, spdi, hgvs, ca_id, rsid, region }) => ({ variant_id, spdi, hgvs, ca_id, rsid, region }))(input)
    delete input.variant_id
    delete input.spdi
    delete input.hgvs
    delete input.rsid
    delete input.ca_id
    delete input.region
    variantIDs = await variantIDSearch(variantInput)
  }
  const variantFilter = isVariantQuery ? 'record._from IN @variantIDs' : ''
  const edgeFilterSts = getEdgeFilters(input)
  const filterStatement = `FILTER ${[variantFilter, edgeFilterSts].filter(Boolean).join(' AND ')}`
  const searchViewName = `${variantsGenomicElementsAFGRCAQtl.db_collection_name as string}_text_en_no_stem_inverted_search_alias`

  const bindVars = isVariantQuery ? { variantIDs } : undefined
  const exactObjects = await executeExactMatchQuery({
    biologicalContext: biologicalContext as string || undefined,
    filterStatement,
    limit,
    page,
    bindVars
  })

  if (exactObjects.length > 0 || biologicalContext === undefined) {
    return exactObjects
  }

  const prefixObjects = await executePrefixMatchQuery({
    biologicalContext: biologicalContext as string,
    filterStatement,
    limit,
    page,
    searchViewName,
    bindVars
  })
  if (prefixObjects.length > 0) {
    return prefixObjects
  }

  const tokenMatchObjects = await executeTokenMatchQuery({
    biologicalContext: biologicalContext as string,
    filterStatement,
    limit,
    page,
    searchViewName,
    bindVars
  })
  if (tokenMatchObjects.length > 0) {
    return tokenMatchObjects
  }

  return await executeLevenshteinMatchQuery({
    biologicalContext: biologicalContext as string,
    filterStatement,
    limit,
    page,
    searchViewName,
    bindVars
  })
}

async function findVariantsFromGenomicElementsQuery (input: paramsFormatType): Promise<any> {
  genomicElementQueryValidation(input)
  const limit = getQueryLimit(input)
  const page = input.page as number
  const biologicalContext = input.biological_context
  delete input.biological_context

  let elementIDs: string[] = []
  const isElementQuery = input.region !== undefined
  if (isElementQuery) {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const elementInput: paramsFormatType = (({ region, type }) => ({ region, type }))(input)
    delete input.region
    delete input.type
    const elementFilters = getFilterStatements(humanGenomicElementSchema, preProcessRegionParam(elementInput))
    const elementQuery = `
      FOR record IN ${humanGenomicElementSchema.db_collection_name as string}
      FILTER ${elementFilters}
      RETURN record._id
    `
    elementIDs = await (await db.query(elementQuery)).all()
  }
  const edgeFilters = getEdgeFilters(input)
  const elementFilter = isElementQuery ? 'record._to IN @elementIDs' : ''
  const combinedFilter = `FILTER ${[elementFilter, edgeFilters].filter(Boolean).join(' AND ')}`
  const searchViewName = `${variantsGenomicElementsAFGRCAQtl.db_collection_name as string}_text_en_no_stem_inverted_search_alias`

  const bindVars = isElementQuery ? { elementIDs } : undefined
  const exactObjects = await executeExactMatchQuery({
    biologicalContext: biologicalContext as string || undefined,
    filterStatement: combinedFilter,
    limit,
    page,
    bindVars
  })

  if (exactObjects.length > 0 || biologicalContext === undefined) {
    return exactObjects
  }

  const prefixObjects = await executePrefixMatchQuery({
    biologicalContext: biologicalContext as string,
    filterStatement: combinedFilter,
    limit,
    page,
    searchViewName,
    bindVars
  })
  if (prefixObjects.length > 0) {
    return prefixObjects
  }

  const tokenMatchObjects = await executeTokenMatchQuery({
    biologicalContext: biologicalContext as string,
    filterStatement: combinedFilter,
    limit,
    page,
    searchViewName,
    bindVars
  })
  if (tokenMatchObjects.length > 0) {
    return tokenMatchObjects
  }

  return await executeLevenshteinMatchQuery({
    biologicalContext: biologicalContext as string,
    filterStatement: combinedFilter,
    limit,
    page,
    searchViewName,
    bindVars
  })
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

const variantsRegionSummary = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/region-summary', description: descriptions.variants_region_summary } })
  .input(z.object({ region: z.string() }))
  .output(regionSummaryFormat)
  .query(async ({ input }) => await findVariantsRegionSummary(input))

const genomicElementsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/genomic-elements', description: descriptions.variants_genomic_elements_edge } })
  .input(variantsQueryFormat)
  .output(genomicElementsFromVariantsOutputFormat)
  .query(async ({ input }) => await findGenomicElementsFromVariantsQuery(input))

const variantsFromGenomicElements = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genomic-elements/variants', description: descriptions.genomic_elements_variants_edge } })
  .input(genomicBiosamplesQuery)
  .output(genomicElementsFromVariantsOutputFormat)
  .query(async ({ input }) => await findVariantsFromGenomicElementsQuery(input))

const genomicElementsPredictionsFromVariant = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/genomic-elements/cell-gene-predictions', description: descriptions.cell_gene_genomic_elements } })
  .input(variantsCommonQueryFormat)
  .output(genomicElementsPredictionsFormat)
  .query(async ({ input }) => await findGenomicElementsPredictionsFromVariantsQuery(input))

export const variantsGenomicElementsRouters = {
  predictionsFromVariants,
  genomicElementsFromVariantsCount,
  genomicElementsPredictionsFromVariant,
  variantsFromGenomicElements,
  genomicElementsFromVariants,
  variantsRegionSummary
}
