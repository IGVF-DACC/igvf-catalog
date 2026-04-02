import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { geneSearch } from '../nodes/genes'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonHumanEdgeParamsFormat, genesCommonQueryFormat, genomicElementCommonQueryFormat } from '../params'
import { getSchema, getCollectionEnumValuesOrThrow } from '../schema'

const MAX_PAGE_SIZE = 500
const METHODS = getCollectionEnumValuesOrThrow('edges', 'genomic_elements_genes', 'method')
const SOURCES = getCollectionEnumValuesOrThrow('edges', 'genomic_elements_genes', 'source')

const genomicElementsGenesEncode2GCrisprSchema = getSchema('data/schemas/edges/genomic_elements_genes.ENCODE2GCRISPR.json')
const genomicElementsGenesIGVFE2GCrisprSchema = getSchema('data/schemas/edges/genomic_elements_genes.IGVFE2GCRISPR.json')
const genomicElementsGenesEncodeElementGeneLinkSchema = getSchema('data/schemas/edges/genomic_elements_genes.EncodeElementGeneLink.json')
const genomicElementToGeneCollectionName = 'genomic_elements_genes'
const genomicElementSchema = getSchema('data/schemas/nodes/genomic_elements.CCRE.json')
const genomicElementCollectionName = genomicElementSchema.db_collection_name as string
const geneSchema = getSchema('data/schemas/nodes/genes.GencodeGene.json')
const geneCollectionName = geneSchema.db_collection_name as string

const edgeQueryFormat = z.object({
  method: z.enum(METHODS).optional(),
  files_fileset: z.string().optional(),
  biosample_term: z.string().optional(),
  biological_context: z.string().optional(),
  source: z.enum(SOURCES).optional()
})

const geneQueryFormat = genesCommonQueryFormat.merge(edgeQueryFormat).merge(commonHumanEdgeParamsFormat)

const genomicElementQueryFormat = genomicElementCommonQueryFormat.omit({
  source: true
}).merge(edgeQueryFormat)
  .merge(commonHumanEdgeParamsFormat)

const elementOutputFormat = z.object({
  _id: z.string(),
  type: z.string().nullish(),
  chr: z.string().nullish(),
  start: z.number().nullish(),
  end: z.number().nullish(),
  name: z.string()
})

const geneOutputFormat = z.object({
  name: z.string(),
  _id: z.string(),
  start: z.number(),
  end: z.number(),
  chr: z.string()
})

const outputFormat = z.array(z.object({
  name: z.string(),
  label: z.string(),
  method: z.string(),
  class: z.string(),
  source: z.string(),
  source_url: z.string(),
  biological_context: z.string(),
  biosample_term: z.string(),
  files_filesets: z.string(),
  score: z.number().nullable(),
  p_value: z.number().or(z.string()).nullish(),
  genomic_element: z.string().or(elementOutputFormat),
  gene: z.string().or(geneOutputFormat)
}))

const buildEdgeFilter = (input: paramsFormatType): string => {
  if (input.files_fileset !== undefined) {
    input.files_filesets = `files_filesets/${input.files_fileset as string}`
    delete input.files_fileset
  }

  if (input.biosample_term !== undefined) {
    input.biosample_term = `ontology_terms/${input.biosample_term as string}`
  }
  // edge filters are the same for all methods
  const filters = getFilterStatements(genomicElementsGenesEncode2GCrisprSchema, input)
  delete input.files_fileset
  delete input.biosample_term
  delete input.biological_context
  delete input.method
  delete input.source
  return filters
}

const buildCombinedFilter = (primaryFilter: string, edgeFilter: string): string => {
  return [primaryFilter, edgeFilter].filter((filter) => filter !== '').join(' AND ') || 'true'
}

function applyLimit (input: paramsFormatType): number {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  return limit
}

function buildQuery (params: {
  collectionName: string
  searchClause?: string
  combinedFilter: string
  page: number
  limit: number
  verbose: boolean
  edgeNameField: 'name' | 'inverse_name'
  sortByKey?: boolean
}): string {
  const { collectionName, searchClause, combinedFilter, page, limit, verbose, edgeNameField, sortByKey } = params
  const sortClause = sortByKey ? 'SORT record._key' : ''
  return `
    LET edgeRecords = (
      FOR record IN ${collectionName}
      ${searchClause ?? ''}
      FILTER ${combinedFilter}
      ${sortClause}
      LIMIT ${page * limit}, ${limit}
      RETURN record
    )
    LET geneIDs = UNIQUE(edgeRecords[*]._to)
    LET elementIDs = UNIQUE(edgeRecords[*]._from)
    LET geneLookup = ${verbose ? `(FOR gene IN ${geneCollectionName} FILTER gene._id IN geneIDs RETURN { [gene._id]: {${getDBReturnStatements(geneSchema).replaceAll('record', 'gene')}} })` : '[]'}
    LET elementLookup = ${verbose ? `(FOR element IN ${genomicElementCollectionName} FILTER element._id IN elementIDs RETURN { [element._id]: {${getDBReturnStatements(genomicElementSchema).replaceAll('record', 'element')}} })` : '[]'}
    LET geneMap = MERGE(geneLookup)
    LET elementMap = MERGE(elementLookup)
    FOR record IN edgeRecords
      LET gene = ${verbose ? 'geneMap[record._to]' : 'record._to'}
      LET element = ${verbose ? 'elementMap[record._from]' : 'record._from'}
      LET base = {
        'gene': gene,
        'genomic_element': element,
        'name': record.${edgeNameField}
      }
      RETURN MERGE(base,
        record.method == 'CRISPR enhancer perturbation screen' ? {
          ${getDBReturnStatements(genomicElementsGenesEncode2GCrisprSchema)}
        } :
        record.method == 'CRISPR FACS screen' ? {
          'score': record.effect_size,
          'p_value': record.p_value_adj,
          ${getDBReturnStatements(genomicElementsGenesIGVFE2GCrisprSchema)}
        } :
        record.method == 'ENCODE-rE2G' ? {
          ${getDBReturnStatements(genomicElementsGenesEncodeElementGeneLinkSchema)}
        } :
        record.method == 'Perturb-seq' ? {
          'score': record.log2FC,
          'p_value': record.p_value_adj,
          ${getDBReturnStatements(genomicElementsGenesIGVFE2GCrisprSchema)}
        } : {}
      )
  `
}

const executeElementsGenesQuery = async (query: string, bindVars?: Record<string, unknown>): Promise<any[]> => {
  const cursor = bindVars ? await db.query(query, bindVars) : await db.query(query)
  return await cursor.all()
}

const executeExactMatchQuery = async ({
  combinedFilter,
  page,
  limit,
  verbose,
  edgeNameField,
  bindVars
}: {
  combinedFilter: string
  page: number
  limit: number
  verbose: boolean
  edgeNameField: 'name' | 'inverse_name'
  bindVars?: Record<string, unknown>
}): Promise<any[]> => {
  const query = buildQuery({
    collectionName: genomicElementToGeneCollectionName,
    combinedFilter,
    page,
    limit,
    verbose,
    edgeNameField,
    sortByKey: true
  })
  return await executeElementsGenesQuery(query, bindVars)
}

const executePrefixMatchQuery = async ({
  searchViewName,
  combinedFilter,
  biologicalContext,
  page,
  limit,
  verbose,
  edgeNameField,
  bindVars
}: {
  searchViewName: string
  combinedFilter: string
  biologicalContext: string
  page: number
  limit: number
  verbose: boolean
  edgeNameField: 'name' | 'inverse_name'
  bindVars?: Record<string, unknown>
}): Promise<any[]> => {
  const searchVal = biologicalContext.replace(/"/g, '\\"')
  const query = buildQuery({
    collectionName: searchViewName,
    searchClause: `SEARCH STARTS_WITH(record.biological_context, "${searchVal}")`,
    combinedFilter,
    page,
    limit,
    verbose,
    edgeNameField
  })
  return await executeElementsGenesQuery(query, bindVars)
}

const executeTokenMatchQuery = async ({
  searchViewName,
  combinedFilter,
  biologicalContext,
  page,
  limit,
  verbose,
  edgeNameField,
  bindVars
}: {
  searchViewName: string
  combinedFilter: string
  biologicalContext: string
  page: number
  limit: number
  verbose: boolean
  edgeNameField: 'name' | 'inverse_name'
  bindVars?: Record<string, unknown>
}): Promise<any[]> => {
  const searchVal = biologicalContext.replace(/"/g, '\\"')
  const query = buildQuery({
    collectionName: searchViewName,
    searchClause: `SEARCH ANALYZER(TOKENS("${searchVal}", "text_en_no_stem") ALL IN record.biological_context, "text_en_no_stem")`,
    combinedFilter,
    page,
    limit,
    verbose,
    edgeNameField
  })
  return await executeElementsGenesQuery(query, bindVars)
}

const executeLevenshteinMatchQuery = async ({
  searchViewName,
  combinedFilter,
  biologicalContext,
  page,
  limit,
  verbose,
  edgeNameField,
  bindVars
}: {
  searchViewName: string
  combinedFilter: string
  biologicalContext: string
  page: number
  limit: number
  verbose: boolean
  edgeNameField: 'name' | 'inverse_name'
  bindVars?: Record<string, unknown>
}): Promise<any[]> => {
  const searchVal = biologicalContext.replace(/"/g, '\\"')
  const query = buildQuery({
    collectionName: searchViewName,
    searchClause: `SEARCH LEVENSHTEIN_MATCH(record.biological_context, "${searchVal}", 1, false)`,
    combinedFilter,
    page,
    limit,
    verbose,
    edgeNameField
  })
  return await executeElementsGenesQuery(query, bindVars)
}

function geneQueryValidation (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['gene_id', 'hgnc_id', 'gene_name', 'alias', 'method', 'files_fileset'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one of those properties must be defined: gene_id, hgnc_id, name, alias, method, files_fileset.'
    })
  }
}

function elementQueryValidation (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['region', 'files_fileset', 'method'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one of those properties must be defined: region, files_fileset, method.'
    })
  }
}

async function findGenomicElementsFromGene (input: paramsFormatType): Promise<any> {
  delete input.organism
  geneQueryValidation(input)
  const limit = applyLimit(input)
  const biologicalContext = input.biological_context as string | undefined
  delete input.biological_context

  let geneIDs: string[] = []
  const isGeneQuery = Object.keys(input).some(item => ['gene_id', 'hgnc_id', 'gene_name', 'alias'].includes(item))
  if (isGeneQuery) {
    const geneInput: paramsFormatType = { gene_id: input.gene_id, hgnc_id: input.hgnc_id, name: input.gene_name, alias: input.alias, organism: 'Homo sapiens', page: 0 }
    delete input.gene_id
    delete input.hgnc_id
    delete input.alias
    delete input.gene_name
    const genes = await geneSearch(geneInput)
    geneIDs = genes.map(gene => `${geneCollectionName}/${gene._id as string}`)
  }

  const edgeFilter = buildEdgeFilter(input)
  const geneFilter = isGeneQuery ? 'record._to IN @geneIDs' : ''
  const baseFilter = buildCombinedFilter(geneFilter, edgeFilter)
  const combinedFilter = biologicalContext
    ? buildCombinedFilter(baseFilter, `record.biological_context == "${biologicalContext.replace(/"/g, '\\"')}"`)
    : baseFilter
  const verbose = input.verbose === 'true'
  const bindVars = isGeneQuery ? { geneIDs } : undefined
  const searchViewName = `${genomicElementToGeneCollectionName}_text_en_no_stem_inverted_search_alias`

  const exactObjects = await executeExactMatchQuery({
    combinedFilter,
    page: input.page as number,
    limit,
    verbose,
    edgeNameField: 'inverse_name',
    bindVars
  })

  if (exactObjects.length > 0 || biologicalContext === undefined) {
    return exactObjects
  }

  const prefixMatchObjects = await executePrefixMatchQuery({
    searchViewName,
    combinedFilter: baseFilter,
    biologicalContext,
    page: input.page as number,
    limit,
    verbose,
    edgeNameField: 'inverse_name',
    bindVars
  })
  if (prefixMatchObjects.length > 0) {
    return prefixMatchObjects
  }

  const tokenMatchObjects = await executeTokenMatchQuery({
    searchViewName,
    combinedFilter: baseFilter,
    biologicalContext,
    page: input.page as number,
    limit,
    verbose,
    edgeNameField: 'inverse_name',
    bindVars
  })
  if (tokenMatchObjects.length > 0) {
    return tokenMatchObjects
  }

  return await executeLevenshteinMatchQuery({
    searchViewName,
    combinedFilter: baseFilter,
    biologicalContext,
    page: input.page as number,
    limit,
    verbose,
    edgeNameField: 'inverse_name',
    bindVars
  })
}

async function findGenesFromGenomicElementsSearch (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  elementQueryValidation(input)
  const limit = applyLimit(input)
  const biologicalContext = input.biological_context as string | undefined
  delete input.biological_context

  let elementIDs: string[] = []
  let isElementQuery = false
  if (input.region !== undefined) {
    isElementQuery = true
    const elementInput: paramsFormatType = { region: input.region, type: input.region_type, source_annotation: input.source_annotation, page: 0 }
    const genomicElementsFilters = getFilterStatements(genomicElementSchema, preProcessRegionParam(elementInput))
    const elementQuery = `
      FOR record IN ${genomicElementCollectionName}
      FILTER ${genomicElementsFilters}
      RETURN record._id
    `
    elementIDs = await (await db.query(elementQuery)).all()
    delete input.region
    delete input.region_type
    delete input.source_annotation
  }

  const edgeFilter = buildEdgeFilter(input)
  const elementFilter = isElementQuery ? 'record._from IN @elementIDs' : ''
  const baseFilter = buildCombinedFilter(elementFilter, edgeFilter)
  const combinedFilter = biologicalContext
    ? buildCombinedFilter(baseFilter, `record.biological_context == "${biologicalContext.replace(/"/g, '\\"')}"`)
    : baseFilter
  const verbose = input.verbose === 'true'
  const bindVars = isElementQuery ? { elementIDs } : undefined
  const searchViewName = `${genomicElementToGeneCollectionName}_text_en_no_stem_inverted_search_alias`

  const exactObjects = await executeExactMatchQuery({
    combinedFilter,
    page: input.page as number,
    limit,
    verbose,
    edgeNameField: 'name',
    bindVars
  })
  if (exactObjects.length > 0 || biologicalContext === undefined) {
    return exactObjects
  }

  const prefixMatchObjects = await executePrefixMatchQuery({
    searchViewName,
    combinedFilter: baseFilter,
    biologicalContext,
    page: input.page as number,
    limit,
    verbose,
    edgeNameField: 'name',
    bindVars
  })
  if (prefixMatchObjects.length > 0) {
    return prefixMatchObjects
  }

  const tokenMatchObjects = await executeTokenMatchQuery({
    searchViewName,
    combinedFilter: baseFilter,
    biologicalContext,
    page: input.page as number,
    limit,
    verbose,
    edgeNameField: 'name',
    bindVars
  })
  if (tokenMatchObjects.length > 0) {
    return tokenMatchObjects
  }

  return await executeLevenshteinMatchQuery({
    searchViewName,
    combinedFilter: baseFilter,
    biologicalContext,
    page: input.page as number,
    limit,
    verbose,
    edgeNameField: 'name',
    bindVars
  })
}

const genomicElementsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/genomic-elements', description: descriptions.genes_genomic_elements } })
  .input(geneQueryFormat)
  .output(outputFormat)
  .query(async ({ input }) => await findGenomicElementsFromGene(input))

const genesFromGenomicElements = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genomic-elements/genes', description: descriptions.genomic_elements_genes } })
  .input(genomicElementQueryFormat)
  .output(outputFormat)
  .query(async ({ input }) => await findGenesFromGenomicElementsSearch(input))

export const genomicElementsGenesRouters = {
  genomicElementsFromGenes,
  genesFromGenomicElements
}
