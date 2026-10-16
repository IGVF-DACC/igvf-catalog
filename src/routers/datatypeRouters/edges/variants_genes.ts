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
import { getCollectionEnumValuesOrThrow, getMergedCollectionSchema, getSchema } from '../schema'

const MAX_PAGE_SIZE = 500

const METHODS = getCollectionEnumValuesOrThrow('edges', 'variants_genes', 'method')
const SOURCES = getCollectionEnumValuesOrThrow('edges', 'variants_genes', 'source')
const LABELS = getCollectionEnumValuesOrThrow('edges', 'variants_genes', 'label')
const NAMES = getCollectionEnumValuesOrThrow('edges', 'variants_genes', 'name')
const INVERSE_NAMES = getCollectionEnumValuesOrThrow('edges', 'variants_genes', 'inverse_name')
// Values calculated from database to optimize range queries
// MAX pvalue = 0.00175877, MAX -log10 pvalue = 306.99234812274665 (from datasets)
// Upper bounds make open-ended client filters (e.g. gte:5) usable with the ZKD sparse index
const MAX_LOG10_PVALUE = 400
const MAX_SLOPE = 8.66426 // i.e. effect_size

export const qtlsSummaryFormat = z.object({
  qtl_type: z.string(),
  neg_log10_pvalue: z.number().nullish(),
  chr: z.string(),
  biological_context: z.string().nullish(),
  effect_size: z.number().nullish(),
  gene: z.object({
    gene_name: z.string(),
    gene_id: z.string(),
    gene_start: z.number(),
    gene_end: z.number()
  }).nullish(),
  name: z.string().nullish(),
  files_filesets: z.string().nullish()
})

const variantsGenesQueryFormat = z.object({
  neg_log10_pvalue: z.string().trim().optional(),
  effect_size: z.string().optional(),
  posterior_inclusion_probability: z.string().optional(),
  log2FC: z.string().optional(),
  significant: z.enum(['true']).optional(),
  biosample_term: z.string().optional(),
  biological_context: z.string().optional(),
  label: z.enum(LABELS).optional(),
  method: z.enum(METHODS).optional(),
  files_fileset: z.string().optional(),
  source: z.enum(SOURCES).optional()
})

const variantsQueryFormat = variantsCommonQueryFormat.merge(variantsGenesQueryFormat).merge(z.object({ name: z.enum(NAMES).optional() })).merge(commonHumanEdgeParamsFormat)
const genesQueryFormat = genesCommonQueryFormat.merge(variantsGenesQueryFormat).merge(z.object({ name: z.enum(INVERSE_NAMES).optional() })).merge(commonHumanEdgeParamsFormat)

export const completeQtlsFormat = z.object({
  gene: z.string().or(geneFormat).nullable(),
  sequence_variant: z.string().or(variantFormat).nullable(),
  intron_chr: z.string().nullish(),
  intron_start: z.number().nullish(),
  intron_end: z.number().nullish(),
  effect_size: z.number().nullish(),
  neg_log10_pvalue: z.number().nullish(),
  neg_log10_pvalue_adj: z.number().nullish(),
  log2FC: z.number().nullish(),
  posterior_inclusion_probability: z.number().nullish(),
  coefficient_stddev: z.number().nullish(),
  power: z.number().nullish(),
  significant: z.boolean().nullish(),
  standard_error: z.number().nullish(),
  z_score: z.number().nullish(),
  credible_set_min_r2: z.number().nullish(),
  method: z.string().nullish(),
  crispr_modality: z.string().nullish(),
  source: z.string(),
  source_url: z.string(),
  label: z.string(),
  p_value: z.number().nullish(),
  chr: z.string().nullish(),
  biological_context: z.string(),
  biosample_term: z.string(),
  study: z.string().or(studyFormat).nullish(),
  name: z.string().nullish(),
  class: z.string().nullish(),
  files_filesets: z.string().nullish()
})

const variantsGenesAFGSRQtl = getSchema('data/schemas/edges/variants_genes.AFGRSQtl.json')
const variantsGenesAFGREQtl = getSchema('data/schemas/edges/variants_genes.AFGREQtl.json')
const variantsGenesEQTLCatalog = getSchema('data/schemas/edges/variants_genes.EQTLCatalog.json')
const variantsGenesCRISPRVariantGene = getSchema('data/schemas/edges/variants_genes.CRISPRVariantGene.json')
// variants_genes holds AFGR sQTL/eQTL, EBI eQTL Catalog, and CRISPR variant-gene edges.
// Filtering must see every source's fields/ranges (e.g. IGVF CRISPR's neg_log10_pvalue,
// EBI's posterior_inclusion_probability), not just one source's schema.
const variantsGenesFilterSchema = getMergedCollectionSchema('edges', 'variants_genes')

const variantSchema = getSchema('data/schemas/nodes/variants.Favor.json')
const geneSchema = getSchema('data/schemas/nodes/genes.GencodeGene.json')
const geneCollectionName = geneSchema.db_collection_name as string
const studySchema = getSchema('data/schemas/nodes/studies.GWAS.json')

// variants_genes is shared with AFGR/EBI eQTL and spliceQTL edges (see variantsGenesFilterSchema
// above) - method/label are hard-restricted below to isolate just the IGVF CRISPR screen
// variant-effect-on-gene-expression edges, so QTL records never leak into these summaries.
const CRISPR_SCREEN_METHOD = 'CRISPR screen'
const CRISPR_SCREEN_LABEL = 'variant effect on gene expression'
// Only IGVF currently produces CRISPR screen variant-gene edges - the file's general SOURCES
// constant also includes AFGR/EBI (QTL-only sources), which could never match here.
const CRISPR_SCREEN_SOURCES = ['IGVF'] as const
const CRISPR_PERTURBATIONS = getCollectionEnumValuesOrThrow('edges', 'variants_genes', 'crispr_modality')
// The only fields on CRISPRVariantGene that represent an effect/association strength, as
// opposed to identifiers, provenance, or the boolean `significant` flag.
const CRISPR_SCORE_FIELDS = ['effect_size', 'log2FC', 'neg_log10_pvalue', 'neg_log10_pvalue_adj', 'power', 'posterior_inclusion_probability', 'coefficient_stddev'] as const

const geneVariantScoreSummaryQueryFormat = z.object({
  gene_id: z.string().trim(),
  score_field: z.enum(CRISPR_SCORE_FIELDS),
  files_fileset: z.string().optional(),
  source: z.enum(CRISPR_SCREEN_SOURCES).optional(),
  biosample_term: z.string().optional(),
  biological_context: z.string().optional(),
  perturbation: z.enum(CRISPR_PERTURBATIONS).optional(),
  // Paginates the groups list itself, not the underlying edges - the aggregation still runs
  // over every matching edge regardless of page/limit, matching the sibling
  // /genes/genomic-elements/score-summary endpoint's pagination convention.
  page: z.number().default(0),
  limit: z.number().optional()
})

const geneVariantScoreSummaryGroupFormat = z.object({
  method: z.string().nullable(),
  source: z.string().nullable(),
  files_filesets: z.string().nullable(),
  biosample_term: z.string().nullable(),
  biological_context: z.string().nullable(),
  perturbation: z.string().nullable(),
  min: z.number().nullable(),
  max: z.number().nullable(),
  edge_count: z.number(),
  numeric_count: z.number(),
  missing_count: z.number(),
  invalid_count: z.number(),
  zero_count: z.number()
})

const geneVariantScoreSummaryFormat = z.object({
  gene_id: z.string(),
  score_field: z.enum(CRISPR_SCORE_FIELDS),
  total_edge_count: z.number(),
  groups: z.array(geneVariantScoreSummaryGroupFormat)
})

function raiseInvalidParameters (param: string): void {
  throw new TRPCError({
    code: 'BAD_REQUEST',
    message: `${param} must be a query range using: gte, lte, gt, or lt. For example: lte:0.001`
  })
}

export async function qtlSummary (input: paramsFormatType): Promise<any> {
  let idxHint = ''
  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = `record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
    idxHint = 'OPTIONS { indexHint: "idx_persistent_files_filesets", forceIndexHint: true }'
    delete input.files_fileset
  }

  let variantClause = ''
  if (Object.keys(input).length !== 0) {
    const variant = (await variantSearch(input))

    if (variant.length === 0) {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: 'Variant not found.'
      })
    }
    variantClause = `record._from == 'variants/${variant[0]._id as string}'`
  } else if (filesetFilter === '') {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one parameter must be defined.'
    })
  }

  const searchClause = [variantClause, filesetFilter].filter(clause => clause !== '').join(' AND ')
  if (searchClause === '') {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one parameter must be defined.'
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
    FOR record IN variants_genes ${idxHint}
    FILTER ${searchClause}
    SORT record._key
    LIMIT ${(input.page as number || 0) * QUERY_LIMIT}, ${QUERY_LIMIT}
    RETURN {
      '_id': record._id,
      qtl_type: record.label,
      neg_log10_pvalue: record.neg_log10_pvalue,
      chr: record.chr OR SPLIT(record.variant_chromosome_position_ref_alt, '_')[0],
      biological_context: record.biological_context,
      effect_size: record.effect_size,
      gene: (${targetQuery})[0],
      name: record.name,
      files_filesets: record.files_filesets
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
  const isInvalidFilter = Object.keys(input).every(item => !['gene_id', 'hgnc_id', 'gene_name', 'region', 'synonym', 'method', 'files_fileset'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one of these properties must be defined: gene_id, hgnc_id, gene_name, region, synonym, method, files_fileset'
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
  if ('neg_log10_pvalue' in input) {
    // Upper bound for ZKD index on (neg_log10_pvalue, effect_size); does not change response values
    restrictiveFiltersArray.push(`record.neg_log10_pvalue <= ${MAX_LOG10_PVALUE}`)
    if (!(input.neg_log10_pvalue as string).includes(':')) {
      raiseInvalidParameters('neg_log10_pvalue')
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
        ${getDBReturnStatements(variantsGenesCRISPRVariantGene)}
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
  const isGeneQuery = Object.keys(input).some(item => ['gene_id', 'hgnc_id', 'gene_name', 'synonym'].includes(item))
  if (isGeneQuery) {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const geneInput: paramsFormatType = (({ gene_id, hgnc_id, gene_name: name, synonym }) => ({ gene_id, hgnc_id, name, synonym, organism: 'Homo sapiens', page: 0 }))(input)
    delete input.gene_id
    delete input.hgnc_id
    delete input.gene_name
    delete input.synonym
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
  const edgeFilters = getFilterStatements(variantsGenesFilterSchema, input)
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

  const searchViewName = `${variantsGenesCRISPRVariantGene.db_collection_name as string}_text_en_no_stem_inverted_search_alias`
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
    return exactObjects
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
    return prefixMatchObjects
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
    return tokenMatchObjects
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
  return levenshteinMatchObjects
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
  const edgeFilters = getFilterStatements(variantsGenesFilterSchema, input)
  let useIndex = ''
  if (!isVariantQuery && filesetFilter !== '') {
    useIndex = 'OPTIONS {indexHint: "idx_persistent_files_filesets", forceIndexHint: true}'
  }
  // combine variantFilter, edgeFilters, restrictiveFilters and filesetFilter
  const baseFilters = [variantFilter, edgeFilters, restrictiveFilters, filesetFilter].filter(Boolean)
  const filterStatement = `FILTER ${baseFilters.join(' AND ')}`
  const exactFilterStatement = biologicalContext
    ? `FILTER ${[...baseFilters, `record.biological_context == "${biologicalContext.replace(/"/g, '\\"')}"`].join(' AND ')}`
    : filterStatement

  const searchViewName = `${variantsGenesCRISPRVariantGene.db_collection_name as string}_text_en_no_stem_inverted_search_alias`
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
    return exactObjects
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
    return prefixMatchObjects
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
    return tokenMatchObjects
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
  return levenshteinMatchObjects
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
    FILTER ${getFilterStatements(geneSchema, preProcessRegionParam(input))}
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

// Aggregates entirely in AQL (COLLECT ... AGGREGATE), same approach as the sibling
// /genes/genomic-elements/score-summary endpoint - MIN/MAX already ignore `null` inputs, so
// feeding them `isNumeric ? rawScore : null` for non-numeric/missing/boolean scores gives
// exactly the "bounds among finite numeric values, null if none exist" semantics for free.
// IS_NUMBER() returns false for both numeric-looking strings and booleans, so neither gets
// miscounted as numeric - they fall into invalid_count instead, per spec.
async function findGeneVariantScoreSummary (input: paramsFormatType): Promise<any> {
  const geneId = input.gene_id as string
  const scoreField = input.score_field as string
  delete input.gene_id
  delete input.score_field
  const limit = getQueryLimit(input)
  const page = input.page as number

  const geneDocs = await (await db.query(
    `FOR g IN ${geneCollectionName} FILTER g._key == @geneId LIMIT 1 RETURN g._id`,
    { geneId }
  )).all()

  if (geneDocs.length === 0) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: `Gene not found: ${geneId}`
    })
  }

  // biological_context must be an exact match here - no prefix/token/Levenshtein fallback
  // search, unlike getVariantFromGene/getGeneFromVariant above.
  const biologicalContext = input.biological_context as string | undefined
  delete input.biological_context

  if (input.files_fileset !== undefined) {
    input.files_filesets = `files_filesets/${input.files_fileset as string}`
    delete input.files_fileset
  }
  if (input.biosample_term !== undefined) {
    input.biosample_term = `ontology_terms/${input.biosample_term as string}`
  }
  // perturbation is the public name for the stored crispr_modality field.
  if (input.perturbation !== undefined) {
    input.crispr_modality = input.perturbation
    delete input.perturbation
  }

  const optionalFilters = getFilterStatements(variantsGenesCRISPRVariantGene, input)
  const filters = [
    'record._to == @geneFullId',
    `record.method == '${CRISPR_SCREEN_METHOD}'`,
    `record.label == '${CRISPR_SCREEN_LABEL}'`,
    optionalFilters
  ].filter((filter) => filter !== '')
  const bindVars: Record<string, unknown> = { geneFullId: geneDocs[0], scoreField, page, limit }
  if (biologicalContext !== undefined) {
    filters.push('record.biological_context == @biologicalContext')
    bindVars.biologicalContext = biologicalContext
  }
  const combinedFilter = filters.join(' AND ')

  // Pagination applies to the groups list, not the underlying edges - total_edge_count is
  // summed over every group before slicing, so it always reflects the full match set
  // regardless of which page is requested. The SORT makes page boundaries deterministic.
  const query = `
    LET allGroups = (
      FOR record IN variants_genes
        FILTER ${combinedFilter}
        LET rawScore = record[@scoreField]
        LET isNumeric = IS_NUMBER(rawScore)
        COLLECT
          method = record.method,
          source = record.source,
          files_filesets = record.files_filesets,
          biosample_term = record.biosample_term,
          biological_context = record.biological_context,
          perturbation = record.crispr_modality
        AGGREGATE
          edge_count = SUM(1),
          numeric_count = SUM(isNumeric ? 1 : 0),
          missing_count = SUM(rawScore == null ? 1 : 0),
          invalid_count = SUM((rawScore != null && !isNumeric) ? 1 : 0),
          zero_count = SUM((isNumeric && rawScore == 0) ? 1 : 0),
          minScore = MIN(isNumeric ? rawScore : null),
          maxScore = MAX(isNumeric ? rawScore : null)
        SORT method, source, files_filesets, biosample_term, biological_context, perturbation
        RETURN {
          method, source, files_filesets, biosample_term, biological_context, perturbation,
          'min': minScore,
          'max': maxScore,
          edge_count, numeric_count, missing_count, invalid_count, zero_count
        }
    )
    RETURN {
      total_edge_count: SUM(allGroups[*].edge_count),
      groups: SLICE(allGroups, @page * @limit, @limit)
    }
  `

  const results = await (await db.query(query, bindVars)).all()
  const summary = results[0]

  return {
    gene_id: geneId,
    score_field: scoreField,
    total_edge_count: summary.total_edge_count,
    groups: summary.groups
  }
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
  .input(singleVariantQueryFormat.merge(z.object({ page: z.number().optional().default(0), limit: z.number().optional(), files_fileset: z.string().optional() })))
  .output(z.array(qtlsSummaryFormat))
  .query(async ({ input }) => await qtlSummary(input))

const genesVariantsScoreSummary = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/variants/score-summary', description: descriptions.genes_variants_score_summary } })
  .input(geneVariantScoreSummaryQueryFormat)
  .output(geneVariantScoreSummaryFormat)
  .query(async ({ input }) => await findGeneVariantScoreSummary(input))

export const variantsGenesRouters = {
  qtlSummaryEndpoint,
  genesFromVariants,
  variantsFromGenes,
  nearestGenes,
  genesVariantsScoreSummary
}
