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

const genomicElementsGenesCrisprElementGeneEncodeSchema = getSchema('data/schemas/edges/genomic_elements_genes.CRISPRElementGeneENCODE.json')
const genomicElementsGenesCrisprElementGeneIgvfSchema = getSchema('data/schemas/edges/genomic_elements_genes.CRISPRElementGeneIGVF.json')
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

const gnrGeneQueryFormat = z.object({
  regulator_gene_id: z.string().optional(),
  regulator_hgnc_id: z.string().optional(),
  regulator_gene_name: z.string().optional(),
  regulator_synonym: z.string().optional(),
  response_gene_id: z.string().optional(),
  response_hgnc_id: z.string().optional(),
  response_gene_name: z.string().optional(),
  response_synonym: z.string().optional(),
  neg_log10_pvalue: z.string().optional(),
  neg_log10_pvalue_adj: z.string().optional(),
  method: z.enum(['CRISPR screen', 'Perturb-seq']).optional(),
  files_fileset: z.string().optional(),
  significant: z.enum(['true']).optional(),
  crispr_modality: z.enum(['knockout', 'interference', 'activation']).optional()
}).merge(commonHumanEdgeParamsFormat).omit({ organism: true, verbose: true })

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
  biological_context: z.string().nullish(),
  biosample_term: z.string().nullish(),
  cell_type: z.string().nullish(),
  cell_type_term: z.string().nullish(),
  files_filesets: z.string(),
  crispr_modality: z.string().nullish(),
  score: z.number().nullish(),
  transcription_start_site: z.number().nullish(),
  rna_pseudobulk_tpm: z.number().nullish(),
  log2FC: z.number().nullish(),
  effect_size: z.number().nullish(),
  z_score: z.number().nullish(),
  t_score: z.number().nullish(),
  p_value: z.number().or(z.string()).nullish(),
  p_value_adj: z.number().or(z.string()).nullish(),
  neg_log10_pvalue: z.number().or(z.string()).nullish(),
  neg_log10_pvalue_adj: z.number().or(z.string()).nullish(),
  genomic_element: z.string().or(elementOutputFormat),
  gene: z.string().or(geneOutputFormat)
}))

const grnOutputFormat = z.object({
  response_gene: z.string(),
  genomic_element: z.object({
    chr: z.string(),
    start: z.number(),
    end: z.number(),
    regulator_gene: z.string()
  }),
  crispr_modality: z.string().nullish(),
  class: z.string(),
  method: z.string(),
  source: z.string(),
  biological_context: z.string(),
  files_filesets: z.string(),
  log2FC: z.number().nullish(),
  neg_log10_pvalue: z.number().or(z.string()).nullish(),
  neg_log10_pvalue_adj: z.number().or(z.string()).nullish(),
  significant: z.boolean().nullish(),
  perturbation_efficiency_log2FC: z.number().nullish(),
  perturbation_efficiency_neg_log10_pvalue: z.number().or(z.string()).nullish(),
  perturbation_efficiency_neg_log10_pvalue_adj: z.number().or(z.string()).nullish(),
  perturbation_efficiency_significant: z.boolean().nullish()
})

const buildEdgeFilter = (input: paramsFormatType): string => {
  if (input.files_fileset !== undefined) {
    input.files_filesets = `files_filesets/${input.files_fileset as string}`
    delete input.files_fileset
  }

  if (input.biosample_term !== undefined) {
    input.biosample_term = `ontology_terms/${input.biosample_term as string}`
  }
  // edge filters are the same for all methods
  const filters = getFilterStatements(genomicElementsGenesCrisprElementGeneEncodeSchema, input)
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
      RETURN {
        'gene': gene,
        'genomic_element': element,
        'name': record.${edgeNameField},
        'class': record.class,
        'label': record.label,
        'method': record.method,
        'source': record.source,
        'source_url': record.source_url,
        'files_filesets': record.files_filesets,
        'biological_context': record.biological_context,
        'biosample_term': record.biosample_term,
        'cell_type': record.cell_type,
        'cell_type_term': record.cell_type_term,
        'crispr_modality': record.crispr_modality,
        'score': record.score,
        'transcription_start_site': record.transcription_start_site,
        'rna_pseudobulk_tpm': record.rna_pseudobulk_tpm,
        'log2FC': record.log2FC,
        'effect_size': record.effect_size,
        'z_score': record.z_score,
        't_score': record.t_score,
        'p_value': record.p_value,
        'p_value_adj': record.p_value_adj,
        'neg_log10_pvalue': record.neg_log10_pvalue,
        'neg_log10_pvalue_adj': record.neg_log10_pvalue_adj
      }
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
  const isInvalidFilter = Object.keys(input).every(item => !['gene_id', 'hgnc_id', 'gene_name', 'synonym', 'method', 'files_fileset'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one of those properties must be defined: gene_id, hgnc_id, name, synonym, method, files_fileset.'
    })
  }
}

function grnQueryValidation (input: paramsFormatType): void {
  const isInvalidRegulatorFilter = Object.keys(input).every(item => !['regulator_gene_id', 'regulator_hgnc_id', 'regulator_gene_name', 'regulator_synonym'].includes(item))
  const isInvalidResponseFilter = Object.keys(input).every(item => !['response_gene_id', 'response_hgnc_id', 'response_gene_name', 'response_synonym'].includes(item))

  if (isInvalidRegulatorFilter && isInvalidResponseFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one of gene must be defined.'
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
  const isGeneQuery = Object.keys(input).some(item => ['gene_id', 'hgnc_id', 'gene_name', 'synonym'].includes(item))
  if (isGeneQuery) {
    const geneInput: paramsFormatType = { gene_id: input.gene_id, hgnc_id: input.hgnc_id, name: input.gene_name, synonym: input.synonym, organism: 'Homo sapiens', page: 0 }
    delete input.gene_id
    delete input.hgnc_id
    delete input.synonym
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

async function grnSearch (input: paramsFormatType): Promise<any> {
  grnQueryValidation(input)
  const limit = applyLimit(input)

  const regulatorGeneInput: paramsFormatType = { _key: input.regulator_gene_id, hgnc: input.regulator_hgnc_id, name: input.regulator_gene_name, synonyms: input.regulator_synonym, organism: 'Homo sapiens', page: 0 }
  const responseGeneInput: paramsFormatType = { _key: input.response_gene_id, hgnc: input.response_hgnc_id, name: input.response_gene_name, synonyms: input.response_synonym, organism: 'Homo sapiens', page: 0 }

  const hasRegulatorInput = Object.keys(regulatorGeneInput).some(key => !['organism', 'page'].includes(key) && regulatorGeneInput[key] !== undefined)
  const hasResponseInput = Object.keys(responseGeneInput).some(key => !['organism', 'page'].includes(key) && responseGeneInput[key] !== undefined)

  let pvalueFilter = ''
  const pvalueFilters: paramsFormatType = {}
  if (input.neg_log10_pvalue !== undefined) {
    pvalueFilters.neg_log10_pvalue = input.neg_log10_pvalue
  }
  if (input.neg_log10_pvalue_adj !== undefined) {
    pvalueFilters.neg_log10_pvalue_adj = input.neg_log10_pvalue_adj
  }
  if (Object.keys(pvalueFilters).length > 0) {
    pvalueFilter = `FILTER ${getFilterStatements(genomicElementsGenesCrisprElementGeneIgvfSchema, pvalueFilters)}`
  }

  let methodFilter = '[\'Perturb-seq\', \'CRISPR screen\']'
  if (input.method !== undefined) {
    methodFilter = `['${input.method as string}']`
  }

  let filesFilesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesFilesetFilter = `AND record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
  }

  let significantFilter = ''
  if (input.significant !== undefined) {
    significantFilter = `AND record.significant == ${input.significant as string}`
  }

  let crisprModalityFilter = ''
  if (input.crispr_modality !== undefined) {
    crisprModalityFilter = `AND record.crispr_modality == '${input.crispr_modality as string}'`
  }

  const responseQuery = `
    FOR gene IN genes
        FILTER ${getFilterStatements(geneSchema, preProcessRegionParam(responseGeneInput)).replaceAll('record', 'gene')}

        FOR record in genomic_elements_genes
          FILTER record._to == gene._id AND record.method IN ${methodFilter} ${filesFilesetFilter} ${significantFilter} ${crisprModalityFilter}
          ${pvalueFilter}
          SORT record._key

          LIMIT ${(input.page as number || 0) * limit}, ${limit}

          LET ge = DOCUMENT(record._from)
          LET perturbationEfficiencyEdge = FIRST(
            FOR se IN genomic_elements_genes
              FILTER se._from == ge._id AND se._to == ge.promoter_of AND se.files_filesets == record.files_filesets
              LIMIT 1
              RETURN se
          )

          RETURN {
          'response_gene': gene.name,
          'genomic_element': { 'start': ge.start, 'end': ge.end, 'chr': ge.chr, 'regulator_gene': DOCUMENT(ge.promoter_of).name },
          'crispr_modality': record.crispr_modality,
          'class': record.class,
          'method': record.method,
          'source': record.source,
          'files_filesets': record.files_filesets,
          'biological_context': record.biological_context,
          'log2FC': record.log2FC,
          'neg_log10_pvalue': record.neg_log10_pvalue,
          'neg_log10_pvalue_adj': record.neg_log10_pvalue_adj,
          'significant': record.significant,
          'perturbation_efficiency_log2FC': perturbationEfficiencyEdge.log2FC,
          'perturbation_efficiency_neg_log10_pvalue': perturbationEfficiencyEdge.neg_log10_pvalue,
          'perturbation_efficiency_neg_log10_pvalue_adj': perturbationEfficiencyEdge.neg_log10_pvalue_adj,
          'perturbation_efficiency_significant': perturbationEfficiencyEdge.significant
        }
  `

  const regulatorQuery = `
    FOR gene IN genes
        FILTER ${getFilterStatements(geneSchema, preProcessRegionParam(regulatorGeneInput)).replaceAll('record', 'gene')}

        FOR ge in genomic_elements
          FILTER ge.promoter_of == gene._id

          FOR record in genomic_elements_genes
            FILTER record._from == ge._id AND record.method IN ${methodFilter} ${filesFilesetFilter} ${significantFilter} ${crisprModalityFilter}
            ${pvalueFilter}
            SORT record._key
            LIMIT ${(input.page as number || 0) * limit}, ${limit}

            LET perturbationEfficiencyEdge = FIRST(
              FOR se IN genomic_elements_genes
                FILTER se._from == ge._id AND se._to == gene._id AND se.files_filesets == record.files_filesets
                LIMIT 1
                RETURN se
            )

            RETURN {
            'response_gene': DOCUMENT(record._to).name,
            'genomic_element': { 'start': ge.start, 'end': ge.end, 'chr': ge.chr, 'regulator_gene': gene.name },
            'crispr_modality': record.crispr_modality,
            'class': record.class,
            'method': record.method,
            'source': record.source,
            'files_filesets': record.files_filesets,
            'biological_context': record.biological_context,
            'log2FC': record.log2FC,
            'neg_log10_pvalue': record.neg_log10_pvalue,
            'neg_log10_pvalue_adj': record.neg_log10_pvalue_adj,
            'significant': record.significant,
            'perturbation_efficiency_log2FC': perturbationEfficiencyEdge.log2FC,
            'perturbation_efficiency_neg_log10_pvalue': perturbationEfficiencyEdge.neg_log10_pvalue,
            'perturbation_efficiency_neg_log10_pvalue_adj': perturbationEfficiencyEdge.neg_log10_pvalue_adj,
            'perturbation_efficiency_significant': perturbationEfficiencyEdge.significant
          }
  `

  const regulatorResponseQuery = `
    FOR regulator_gene IN genes
        FILTER ${getFilterStatements(geneSchema, preProcessRegionParam(regulatorGeneInput)).replaceAll('record', 'regulator_gene')}

        FOR response_gene IN genes
            FILTER ${getFilterStatements(geneSchema, preProcessRegionParam(responseGeneInput)).replaceAll('record', 'response_gene')}

            FOR record in genomic_elements_genes
              FILTER record._to == response_gene._id AND record.method IN ${methodFilter} ${filesFilesetFilter} ${significantFilter} ${crisprModalityFilter}
              ${pvalueFilter}

              FOR ge IN genomic_elements
                FILTER ge._id == record._from AND ge.promoter_of == regulator_gene._id
                SORT record._key
                LIMIT ${(input.page as number || 0) * limit}, ${limit}

                LET perturbationEfficiencyEdge = FIRST(
                  FOR se IN genomic_elements_genes
                    FILTER se._from == ge._id AND se._to == regulator_gene._id AND se.files_filesets == record.files_filesets
                    LIMIT 1
                    RETURN se
                )

                RETURN {
                  'response_gene': response_gene.name,
                  'genomic_element': { 'start': ge.start, 'end': ge.end, 'chr': ge.chr, 'regulator_gene': regulator_gene.name },
                  'crispr_modality': record.crispr_modality,
                  'class': record.class,
                  'method': record.method,
                  'source': record.source,
                  'files_filesets': record.files_filesets,
                  'biological_context': record.biological_context,
                  'log2FC': record.log2FC,
                  'neg_log10_pvalue': record.neg_log10_pvalue,
                  'neg_log10_pvalue_adj': record.neg_log10_pvalue_adj,
                  'significant': record.significant,
                  'perturbation_efficiency_log2FC': perturbationEfficiencyEdge.log2FC,
                  'perturbation_efficiency_neg_log10_pvalue': perturbationEfficiencyEdge.neg_log10_pvalue,
                  'perturbation_efficiency_neg_log10_pvalue_adj': perturbationEfficiencyEdge.neg_log10_pvalue_adj,
                  'perturbation_efficiency_significant': perturbationEfficiencyEdge.significant
              }
  `

  let query = ''
  if (hasRegulatorInput && hasResponseInput) {
    query = regulatorResponseQuery
  } else if (hasRegulatorInput) {
    query = regulatorQuery
  } else if (hasResponseInput) {
    query = responseQuery
  }

  const objs = (await db.query(query)).all()
  if (Array.isArray(objs) && objs.length > 0) {
    return await objs
  }
  return await objs
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

const grn = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/gene-regulatory-network', description: descriptions.grn } })
  .input(gnrGeneQueryFormat)
  .output(z.array(grnOutputFormat))
  .query(async ({ input }) => await grnSearch(input))

export const genomicElementsGenesRouters = {
  genomicElementsFromGenes,
  genesFromGenomicElements,
  grn
}
