import { z } from 'zod'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam, validRegion } from '../_helpers'
import { QUERY_LIMIT } from '../../../constants'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { geneFormat, geneSearch } from '../nodes/genes'
import { commonHumanEdgeParamsFormat, genesCommonQueryFormat, variantsCommonQueryFormat } from '../params'
import { variantSearch, singleVariantQueryFormat, variantFormat, variantIDSearch } from '../nodes/variants'
import { studyFormat } from '../nodes/studies'
import { getCollectionEnumValuesOrThrow, getSchema } from '../schema'

const MAX_PAGE_SIZE = 500

const METHODS = getCollectionEnumValuesOrThrow('edges', 'variants_genes', 'method')
const SOURCES = getCollectionEnumValuesOrThrow('edges', 'variants_genes', 'source')
// Values calculated from database to optimize range queries
// MAX pvalue = 0.00175877, MAX -log10 pvalue = 306.99234812274665 (from datasets)
const MAX_LOG10_PVALUE = 400
const MAX_SLOPE = 8.66426 // i.e. effect_size

const qtlsSummaryFormat = z.object({
  qtl_type: z.string(),
  log10pvalue: z.number().nullish(),
  chr: z.string(),
  biological_context: z.string().nullish(),
  effect_size: z.number().nullish(),
  gene: z.object({
    gene_name: z.string(),
    gene_id: z.string(),
    gene_start: z.number(),
    gene_end: z.number()
  }).nullish(),
  name: z.string().nullish()
})

const variantsGenesQueryFormat = z.object({
  log10pvalue: z.string().trim().optional(),
  effect_size: z.string().optional(),
  biosample_term: z.string().optional(),
  biological_context: z.string().optional(),
  label: z.enum(['eQTL', 'spliceQTL', 'variant effect on gene expression']).optional(),
  method: z.enum(METHODS).optional(),
  files_fileset: z.string().optional(),
  source: z.enum(SOURCES).optional()
})

const variantsQueryFormat = variantsCommonQueryFormat.merge(variantsGenesQueryFormat).merge(z.object({ name: z.enum(['modulates expression of', 'modulates splicing of']).optional() })).merge(commonHumanEdgeParamsFormat)
const genesQueryFormat = genesCommonQueryFormat.merge(variantsGenesQueryFormat).merge(z.object({ name: z.enum(['expression modulated by', 'splicing modulated by']).optional() })).merge(commonHumanEdgeParamsFormat)

const completeQtlsFormat = z.object({
  gene: z.string().or(geneFormat).nullable(),
  sequence_variant: z.string().or(variantFormat).nullable(),
  intron_chr: z.string().nullish(),
  intron_start: z.string().nullish(),
  intron_end: z.string().nullish(),
  effect_size: z.number().nullish(),
  log10pvalue: z.number().or(z.string()).nullish(),
  fdr_nlog10: z.number().nullish(),
  log2_fold_change: z.number().nullish(),
  p_nominal_nlog10: z.number().nullish(),
  posterior_inclusion_probability: z.number().nullish(),
  beta: z.number().nullish(),
  standard_error: z.number().nullish(),
  z_score: z.number().nullish(),
  credible_set_min_r2: z.number().nullish(),
  method: z.string().nullish(),
  source: z.string(),
  source_url: z.string(),
  label: z.string(),
  p_value: z.number().nullish(),
  chr: z.string().nullish(),
  biological_context: z.string(),
  biosample_term: z.string(),
  study: z.string().or(studyFormat).nullish(),
  name: z.string().nullish(),
  class: z.string().nullish()
})

const variantsGenesAFGSRQtl = getSchema('data/schemas/edges/variants_genes.AFGRSQtl.json')
const variantsGenesAFGREQtl = getSchema('data/schemas/edges/variants_genes.AFGREQtl.json')
const variantsGenesEQTLCatalog = getSchema('data/schemas/edges/variants_genes.EQTLCatalog.json')
const variantsGenesVariantEFFECTSAdapter = getSchema('data/schemas/edges/variants_genes.VariantEFFECTSAdapter.json')

const variantSchema = getSchema('data/schemas/nodes/variants.Favor.json')
const geneSchema = getSchema('data/schemas/nodes/genes.GencodeGene.json')
const geneCollectionName = geneSchema.db_collection_name as string
const studySchema = getSchema('data/schemas/nodes/studies.GWAS.json')

function raiseInvalidParameters (param: string): void {
  throw new TRPCError({
    code: 'BAD_REQUEST',
    message: `${param} must be a query range using: gte, lte, gt, or lt. For example: lte:0.001`
  })
}

export async function qtlSummary (input: paramsFormatType): Promise<any> {
  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = ` AND record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
    delete input.files_fileset
  }

  input.page = 0
  const variant = (await variantSearch(input))

  if (variant.length === 0) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Variant not found.'
    })
  }

  const targetQuery = `FOR otherRecord IN genes
  FILTER otherRecord._id == record._to
  RETURN {
    gene_name: otherRecord.name,
    gene_id: otherRecord._key,
    gene_start: otherRecord.start,
    gene_end: otherRecord.end,
  }
  `

  const query = `
    FOR record IN variants_genes
    FILTER record._from == 'variants/${variant[0]._id as string}' ${filesetFilter}
    RETURN {
      qtl_type: record.label,
      log10pvalue: record.log10pvalue or record.p_nominal_nlog10,
      chr: record.chr OR SPLIT(record.variant_chromosome_position_ref_alt, '_')[0] OR '${variant[0].chr as string}',
      biological_context: record.biological_context,
      effect_size: record.effect_size,
      'gene': (${targetQuery})[0],
      'name': record.name
    }
  `
  return await (await db.query(query)).all()
}

export function validateVariantInput (input: paramsFormatType): void {
  const isInvalidInput = Object.keys(input).every(item => !['spdi', 'hgvs', 'rsid', 'ca_id', 'variant_id', 'region', 'method', 'files_fileset'].includes(item))
  if (isInvalidInput) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one of these properties must be defined: spdi, hgvs, rsid, ca_id, variant_id, region, method, files_fileset'
    })
  }
}

function validateGeneInput (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['gene_id', 'hgnc_id', 'gene_name', 'region', 'alias', 'method', 'files_fileset'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one of these properties must be defined: gene_id, hgnc_id, gene_name, region, alias, method, files_fileset'
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

const getRestrictiveFiltersArray = (input: paramsFormatType): string[] => {
  const restrictiveFiltersArray: string[] = []
  if ('log10pvalue' in input) {
    restrictiveFiltersArray.push(`record.log10pvalue <= ${MAX_LOG10_PVALUE}`)
    if (!(input.log10pvalue as string).includes(':')) {
      raiseInvalidParameters('log10pvalue')
    }
  }
  if ('effect_size' in input) {
    restrictiveFiltersArray.push(`record.effect_size <= ${MAX_SLOPE}`)
    if (!(input.effect_size as string).includes(':')) {
      raiseInvalidParameters('effect_size')
    }
  }
  return restrictiveFiltersArray
}

const getFilesetFilter = (input: paramsFormatType): string => {
  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = `record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
    delete input.files_fileset
  }
  return filesetFilter
}

const buildVariantsGenesQuery = ({
  collectionName,
  useIndex,
  searchClause,
  filterStatement,
  limit,
  page,
  verbose,
  nameField
}: {
  collectionName: string
  useIndex: string
  searchClause?: string
  filterStatement: string
  limit: number
  page: number
  verbose: boolean
  nameField: 'name' | 'inverse_name'
}): string => `
    LET edgeRecord = (
      FOR record IN ${collectionName} ${useIndex}
      ${searchClause ?? ''}
      ${filterStatement}
      SORT record._key
      LIMIT ${page * limit}, ${limit}
      RETURN record
    )
    LET studyIDs = UNIQUE(edgeRecord[*].study)
    LET geneIDs = UNIQUE(edgeRecord[*]._to)
    LET variantIDs = UNIQUE(edgeRecord[*]._from)

    LET studyLookup = ${verbose
  ? `(
      FOR s IN studies
      FILTER s._id IN studyIDs
      RETURN { [s._id]: {${getDBReturnStatements(studySchema).replaceAll('record', 's')}} }
    )`
  : '[]'}
    LET geneLookup = ${verbose
  ? `(
      FOR g IN genes
      FILTER g._id IN geneIDs
      RETURN { [g._id]: {${getDBReturnStatements(geneSchema).replaceAll('record', 'g')}} }
    )`
  : '[]'}
    LET variantLookup = ${verbose
  ? `(
      FOR v IN variants
      FILTER v._id IN variantIDs
      RETURN { [v._id]: {${getDBReturnStatements(variantSchema).replaceAll('record', 'v')}} }
    )`
  : '[]'}

    LET sMap = MERGE(studyLookup)
    LET gMap = MERGE(geneLookup)
    LET vMap = MERGE(variantLookup)

    FOR record IN edgeRecord
    LET variant = ${verbose ? 'vMap[record._from]' : 'record._from'}
    LET gene = ${verbose ? 'gMap[record._to]' : 'record._to'}
    LET study = ${verbose ? 'sMap[record.study]' : 'record.study'}
    LET base = {
      'sequence_variant': variant,
      'gene': gene,
      'name': record.${nameField}
    }
    RETURN MERGE(base,
      record.source == 'IGVF' ? {
        ${getDBReturnStatements(variantsGenesVariantEFFECTSAdapter)}
      } : record.source == 'AFGR' && record.label == 'spliceQTL' ? {
        ${getDBReturnStatements(variantsGenesAFGSRQtl)}
      } : record.source == 'AFGR' && record.label == 'eQTL' ? {
        ${getDBReturnStatements(variantsGenesAFGREQtl)}
      } : record.source == 'EBI' ? {
        study: study,
        ${getDBReturnStatements(variantsGenesEQTLCatalog)}
      } : {}
    )
  `

const executeVariantsGenesQuery = async (query: string, bindVars?: Record<string, unknown>): Promise<any[]> => {
  const cursor = bindVars ? await db.query(query, bindVars) : await db.query(query)
  return await cursor.all()
}

const executeExactMatchQuery = async ({
  collectionName,
  useIndex,
  filterStatement,
  limit,
  page,
  verbose,
  nameField,
  bindVars
}: {
  collectionName: string
  useIndex: string
  filterStatement: string
  limit: number
  page: number
  verbose: boolean
  nameField: 'name' | 'inverse_name'
  bindVars?: Record<string, unknown>
}): Promise<any[]> => {
  const query = buildVariantsGenesQuery({
    collectionName,
    useIndex,
    filterStatement,
    limit,
    page,
    verbose,
    nameField
  })
  return await executeVariantsGenesQuery(query, bindVars)
}

const executePrefixMatchQuery = async ({
  collectionName,
  filterStatement,
  biologicalContext,
  limit,
  page,
  verbose,
  nameField,
  bindVars
}: {
  collectionName: string
  filterStatement: string
  biologicalContext: string
  limit: number
  page: number
  verbose: boolean
  nameField: 'name' | 'inverse_name'
  bindVars?: Record<string, unknown>
}): Promise<any[]> => {
  const searchVal = biologicalContext.replace(/"/g, '\\"')
  const query = buildVariantsGenesQuery({
    collectionName,
    useIndex: '',
    searchClause: `SEARCH STARTS_WITH(record.biological_context, "${searchVal}")`,
    filterStatement,
    limit,
    page,
    verbose,
    nameField
  })
  return await executeVariantsGenesQuery(query, bindVars)
}

const executeTokenMatchQuery = async ({
  collectionName,
  filterStatement,
  biologicalContext,
  limit,
  page,
  verbose,
  nameField,
  bindVars
}: {
  collectionName: string
  filterStatement: string
  biologicalContext: string
  limit: number
  page: number
  verbose: boolean
  nameField: 'name' | 'inverse_name'
  bindVars?: Record<string, unknown>
}): Promise<any[]> => {
  const searchVal = biologicalContext.replace(/"/g, '\\"')
  const query = buildVariantsGenesQuery({
    collectionName,
    useIndex: '',
    searchClause: `SEARCH ANALYZER(TOKENS("${searchVal}", "text_en_no_stem") ALL IN record.biological_context, "text_en_no_stem")`,
    filterStatement,
    limit,
    page,
    verbose,
    nameField
  })
  return await executeVariantsGenesQuery(query, bindVars)
}

const executeLevenshteinMatchQuery = async ({
  collectionName,
  filterStatement,
  biologicalContext,
  limit,
  page,
  verbose,
  nameField,
  bindVars
}: {
  collectionName: string
  filterStatement: string
  biologicalContext: string
  limit: number
  page: number
  verbose: boolean
  nameField: 'name' | 'inverse_name'
  bindVars?: Record<string, unknown>
}): Promise<any[]> => {
  const searchVal = biologicalContext.replace(/"/g, '\\"')
  const query = buildVariantsGenesQuery({
    collectionName,
    useIndex: '',
    searchClause: `SEARCH LEVENSHTEIN_MATCH(record.biological_context, "${searchVal}", 1, false)`,
    filterStatement,
    limit,
    page,
    verbose,
    nameField
  })
  return await executeVariantsGenesQuery(query, bindVars)
}

const normalizeLog10Pvalue = (objects: any[]): any[] => {
  for (let index = 0; index < objects.length; index++) {
    const element = objects[index]
    if (element.log10pvalue === MAX_LOG10_PVALUE) {
      objects[index].log10pvalue = 'inf'
    }
  }
  return objects
}

async function getVariantFromGene (input: paramsFormatType): Promise<any[]> {
  validateGeneInput(input)
  delete input.organism
  const verbose = input.verbose === 'true'
  delete input.verbose

  if (input.name !== undefined) {
    input.inverse_name = input.name
    delete input.name
  }

  const restrictiveFiltersArray = getRestrictiveFiltersArray(input)
  const restrictiveFilters = restrictiveFiltersArray.join(' AND ')
  const filesetFilter = getFilesetFilter(input)
  const biologicalContext = input.biological_context as string | undefined
  delete input.biological_context
  let geneIDs: string[] = []
  const isGeneQuery = Object.keys(input).some(item => ['gene_id', 'hgnc_id', 'gene_name', 'alias'].includes(item))
  if (isGeneQuery) {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const geneInput: paramsFormatType = (({ gene_id, hgnc_id, gene_name: name, alias }) => ({ gene_id, hgnc_id, name, alias, organism: 'Homo sapiens', page: 0 }))(input)
    delete input.gene_id
    delete input.hgnc_id
    delete input.gene_name
    delete input.alias
    delete input.organism
    const genes = await geneSearch(geneInput)
    geneIDs = genes.map(gene => `${geneCollectionName}/${gene._id as string}`)
  }
  const limit = getQueryLimit(input)

  let useIndex = ''
  const geneFilter = isGeneQuery ? 'record._to IN @geneIDs' : ''
  if (input.biosample_term !== undefined) {
    input.biosample_term = `ontology_terms/${input.biosample_term as string}`
  }
  const edgeFilters = getFilterStatements(variantsGenesAFGSRQtl, input)
  if (!isGeneQuery) {
    useIndex = 'OPTIONS {indexHint: "idx_persistent_method", forceIndexHint: true}'
    if (filesetFilter !== '') {
      useIndex = 'OPTIONS {indexHint: "idx_persistent_files_filesets", forceIndexHint: true}'
    }
  }
  // combine geneFilter, edgeFilters, restrictiveFilters and filesetFilter
  const baseFilters = [geneFilter, edgeFilters, restrictiveFilters, filesetFilter].filter(Boolean)
  const filterStatement = `FILTER ${baseFilters.join(' AND ')}`
  const exactFilterStatement = biologicalContext
    ? `FILTER ${[...baseFilters, `record.biological_context == "${biologicalContext.replace(/"/g, '\\"')}"`].join(' AND ')}`
    : filterStatement

  const searchViewName = `${variantsGenesAFGSRQtl.db_collection_name as string}_text_en_no_stem_inverted_search_alias`
  const bindVars = isGeneQuery ? { geneIDs } : undefined

  const exactObjects = await executeExactMatchQuery({
    collectionName: 'variants_genes',
    useIndex,
    filterStatement: exactFilterStatement,
    limit,
    page: input.page as number,
    verbose,
    nameField: 'inverse_name',
    bindVars
  })
  if (exactObjects.length > 0 || biologicalContext === undefined) {
    return normalizeLog10Pvalue(exactObjects)
  }

  const prefixMatchObjects = await executePrefixMatchQuery({
    collectionName: searchViewName,
    filterStatement,
    biologicalContext,
    limit,
    page: input.page as number,
    verbose,
    nameField: 'inverse_name',
    bindVars
  })
  if (prefixMatchObjects.length > 0) {
    return normalizeLog10Pvalue(prefixMatchObjects)
  }

  const tokenMatchObjects = await executeTokenMatchQuery({
    collectionName: searchViewName,
    filterStatement,
    biologicalContext,
    limit,
    page: input.page as number,
    verbose,
    nameField: 'inverse_name',
    bindVars
  })
  if (tokenMatchObjects.length > 0) {
    return normalizeLog10Pvalue(tokenMatchObjects)
  }

  const levenshteinMatchObjects = await executeLevenshteinMatchQuery({
    collectionName: searchViewName,
    filterStatement,
    biologicalContext,
    limit,
    page: input.page as number,
    verbose,
    nameField: 'inverse_name',
    bindVars
  })
  return normalizeLog10Pvalue(levenshteinMatchObjects)
}

async function getGeneFromVariant (input: paramsFormatType): Promise<any[]> {
  validateVariantInput(input)
  delete input.organism
  const verbose = input.verbose === 'true'
  delete input.verbose

  const restrictiveFiltersArray = getRestrictiveFiltersArray(input)
  const restrictiveFilters = restrictiveFiltersArray.join(' AND ')
  const filesetFilter = getFilesetFilter(input)
  const biologicalContext = input.biological_context as string | undefined
  delete input.biological_context
  let variantIDs: string[] = []
  const isVariantQuery = Object.keys(input).some(item => ['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id', 'region'].includes(item))
  if (isVariantQuery) {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const variantInput: paramsFormatType = (({ variant_id, spdi, hgvs, rsid, ca_id, region }) => ({ variant_id, spdi, hgvs, rsid, ca_id, region }))(input)
    delete input.variant_id
    delete input.spdi
    delete input.hgvs
    delete input.rsid
    delete input.region
    delete input.ca_id
    variantIDs = await variantIDSearch(variantInput)
  }
  const limit = getQueryLimit(input)
  const variantFilter = isVariantQuery ? 'record._from IN @variantIDs' : ''
  if (input.biosample_term !== undefined) {
    input.biosample_term = `ontology_terms/${input.biosample_term as string}`
  }
  const edgeFilters = getFilterStatements(variantsGenesAFGSRQtl, input)
  let useIndex = ''
  if (!isVariantQuery) {
    useIndex = 'OPTIONS {indexHint: "idx_persistent_method", forceIndexHint: true}'
    if (filesetFilter !== '') {
      useIndex = 'OPTIONS {indexHint: "idx_persistent_files_filesets", forceIndexHint: true}'
    }
  }
  // combine variantFilter, edgeFilters, restrictiveFilters and filesetFilter
  const baseFilters = [variantFilter, edgeFilters, restrictiveFilters, filesetFilter].filter(Boolean)
  const filterStatement = `FILTER ${baseFilters.join(' AND ')}`
  const exactFilterStatement = biologicalContext
    ? `FILTER ${[...baseFilters, `record.biological_context == "${biologicalContext.replace(/"/g, '\\"')}"`].join(' AND ')}`
    : filterStatement

  const searchViewName = `${variantsGenesAFGSRQtl.db_collection_name as string}_text_en_no_stem_inverted_search_alias`
  const bindVars = isVariantQuery ? { variantIDs } : undefined

  const exactObjects = await executeExactMatchQuery({
    collectionName: 'variants_genes',
    useIndex,
    filterStatement: exactFilterStatement,
    limit,
    page: input.page as number,
    verbose,
    nameField: 'name',
    bindVars
  })
  if (exactObjects.length > 0 || biologicalContext === undefined) {
    return normalizeLog10Pvalue(exactObjects)
  }

  const prefixMatchObjects = await executePrefixMatchQuery({
    collectionName: searchViewName,
    filterStatement,
    biologicalContext,
    limit,
    page: input.page as number,
    verbose,
    nameField: 'name',
    bindVars
  })
  if (prefixMatchObjects.length > 0) {
    return normalizeLog10Pvalue(prefixMatchObjects)
  }

  const tokenMatchObjects = await executeTokenMatchQuery({
    collectionName: searchViewName,
    filterStatement,
    biologicalContext,
    limit,
    page: input.page as number,
    verbose,
    nameField: 'name',
    bindVars
  })
  if (tokenMatchObjects.length > 0) {
    return normalizeLog10Pvalue(tokenMatchObjects)
  }

  const levenshteinMatchObjects = await executeLevenshteinMatchQuery({
    collectionName: searchViewName,
    filterStatement,
    biologicalContext,
    limit,
    page: input.page as number,
    verbose,
    nameField: 'name',
    bindVars
  })
  return normalizeLog10Pvalue(levenshteinMatchObjects)
}

async function nearestGeneSearch (input: paramsFormatType): Promise<any[]> {
  const regionParams = validRegion(input.region as string)

  if (regionParams === null) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Region format invalid. Please use the format as the example: "chr1:12345-54321"'
    })
  }

  const inRegionQuery = `
    FOR record in genes
    FILTER ${getFilterStatements(variantSchema, preProcessRegionParam(input))}
    RETURN {${getDBReturnStatements(geneSchema)}}
  `

  const codingRegionGenes = await (await db.query(inRegionQuery)).all()

  if (codingRegionGenes.length !== 0) {
    return codingRegionGenes
  }

  const nearestQuery = `
    LET LEFT = (
      FOR record in genes
      FILTER record.chr == '${regionParams[1]}' and record.end < ${regionParams[2]}
      SORT record.end DESC
      LIMIT 1
      RETURN {${getDBReturnStatements(geneSchema)}}
    )

    LET RIGHT = (
      FOR record in genes
      FILTER record.chr == '${regionParams[1]}' and record.start > ${regionParams[3]}
      SORT record.start
      LIMIT 1
      RETURN {${getDBReturnStatements(geneSchema)}}
    )

    RETURN UNION(LEFT, RIGHT)
  `

  const nearestGenes = await (await db.query(nearestQuery)).all()
  if (nearestGenes !== undefined) {
    return nearestGenes[0]
  }

  return []
}

const genesFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/genes', description: descriptions.variants_genes } })
  .input(variantsQueryFormat)
  .output(z.array(completeQtlsFormat))
  .query(async ({ input }) => await getGeneFromVariant(input))

const variantsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/variants', description: descriptions.genes_variants } })
  .input(genesQueryFormat)
  .output(z.array(completeQtlsFormat))
  .query(async ({ input }) => await getVariantFromGene(input))

const nearestGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/nearest-genes', description: descriptions.nearest_genes } })
  .input(z.object({ region: z.string().trim() }))
  .output(z.array(geneFormat))
  .query(async ({ input }) => await nearestGeneSearch(input))

const qtlSummaryEndpoint = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/genes/summary', description: descriptions.variants_genes_summary } })
  .input(singleVariantQueryFormat.merge(z.object({ files_fileset: z.string().optional() })))
  .output(z.array(qtlsSummaryFormat))
  .query(async ({ input }) => await qtlSummary(input))

export const variantsGenesRouters = {
  qtlSummaryEndpoint,
  genesFromVariants,
  variantsFromGenes,
  nearestGenes
}
