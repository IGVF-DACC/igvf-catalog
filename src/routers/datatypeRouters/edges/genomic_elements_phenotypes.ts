import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonHumanEdgeParamsFormat, genomicElementCommonQueryFormat } from '../params'
import { getSchema, getCollectionEnumValuesOrThrow } from '../schema'

const MAX_PAGE_SIZE = 500
const METHODS = getCollectionEnumValuesOrThrow('edges', 'genomic_elements_phenotypes', 'method')
const SOURCES = getCollectionEnumValuesOrThrow('edges', 'genomic_elements_phenotypes', 'source')

const genomicElementsPhenotypesSchema = getSchema('data/schemas/edges/genomic_elements_phenotypes.CRISPR_E2P.json')
const genomicElementToPhenotypeCollectionName = 'genomic_elements_phenotypes'
const genomicElementSchema = getSchema('data/schemas/nodes/genomic_elements.CCRE.json')
const genomicElementCollectionName = genomicElementSchema.db_collection_name as string
const ontologyCollectionName = 'ontology_terms'

const edgeQueryFormat = z.object({
  method: z.enum(METHODS).optional(),
  files_fileset: z.string().optional(),
  biosample_term: z.string().optional(),
  biological_context: z.string().optional(),
  source: z.enum(SOURCES).optional(),
  phenotype_id: z.string().trim().optional(),
  significant: z.enum(['true', 'false']).optional()
})

const genomicElementQueryFormat = genomicElementCommonQueryFormat.omit({
  source: true
}).merge(edgeQueryFormat)
  .merge(commonHumanEdgeParamsFormat)

const phenotypeQueryFormat = z.object({
  phenotype_id: z.string().trim().optional(),
  phenotype_name: z.string().trim().optional()
}).merge(edgeQueryFormat.omit({ phenotype_id: true })).merge(commonHumanEdgeParamsFormat)

const elementOutputFormat = z.object({
  _id: z.string(),
  type: z.string().nullish(),
  chr: z.string().nullish(),
  start: z.number().nullish(),
  end: z.number().nullish(),
  name: z.string()
})

const phenotypeOutputFormat = z.object({
  phenotype_id: z.string(),
  phenotype_name: z.string().nullish()
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
  crispr_modality: z.string().nullish(),
  z_score: z.number().nullish(),
  p_value: z.number().nullish(),
  neg_log10_pvalue: z.number().nullish(),
  significant: z.boolean().nullish(),
  num_guides: z.number().nullish(),
  hit_guide_count: z.number().nullish(),
  nonhit_guide_count: z.number().nullish(),
  fraction_hit: z.number().nullish(),
  genomic_element: z.string().or(elementOutputFormat),
  phenotype: z.string().or(phenotypeOutputFormat)
}))

function validateQuery (input: paramsFormatType, requiredKeys: string[]): void {
  const definedKeysCount = requiredKeys.filter(key => key in input && input[key] !== undefined).length
  if (definedKeysCount < 1) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: `At least one of these properties must be defined: ${requiredKeys.join(', ')}.`
    })
  }
}

function applyLimit (input: paramsFormatType): number {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  return limit
}

function buildEdgeFilter (input: paramsFormatType): string {
  if (input.files_fileset !== undefined) {
    input.files_filesets = `files_filesets/${input.files_fileset as string}`
    delete input.files_fileset
  }
  if (input.biosample_term !== undefined) {
    input.biosample_term = `ontology_terms/${input.biosample_term as string}`
  }
  if (input.phenotype_id !== undefined) {
    input._to = `ontology_terms/${input.phenotype_id as string}`
    delete input.phenotype_id
  }
  if (input.significant !== undefined) {
    input.significant = input.significant === 'true'
  }

  const filters = getFilterStatements(genomicElementsPhenotypesSchema, input)
  delete input.files_filesets
  delete input.biosample_term
  delete input.biological_context
  delete input.method
  delete input.source
  delete input._to
  delete input.significant
  return filters
}

async function resolvePhenotypeIds (input: paramsFormatType): Promise<string[]> {
  if (input.phenotype_id !== undefined) {
    const phenotypeId = `ontology_terms/${input.phenotype_id as string}`
    delete input.phenotype_id
    return [phenotypeId]
  }

  if (input.phenotype_name === undefined) {
    return []
  }

  const phenotypeName = input.phenotype_name as string
  delete input.phenotype_name

  let phenotypes = await (await db.query(`
    FOR record IN ${ontologyCollectionName}
    FILTER record.name == @phenotypeName
    RETURN record._id
  `, { phenotypeName })).all()

  if (phenotypes.length === 0) {
    phenotypes = await (await db.query(`
      FOR record IN ontology_terms_text_en_no_stem_inverted_search_alias
      SEARCH TOKENS(@phenotypeName, "text_en_no_stem") ALL IN record.name
      SORT BM25(record) DESC
      RETURN record._id
    `, { phenotypeName })).all()
  }
  return phenotypes
}

function buildQuery (params: {
  combinedFilter: string
  page: number
  limit: number
  verbose: boolean
}): string {
  const { combinedFilter, page, limit, verbose } = params
  return `
    LET edgeRecords = (
      FOR record IN ${genomicElementToPhenotypeCollectionName}
      FILTER ${combinedFilter}
      SORT record._key
      LIMIT ${page * limit}, ${limit}
      RETURN record
    )
    LET phenotypeIDs = UNIQUE(edgeRecords[*]._to)
    LET elementIDs = UNIQUE(edgeRecords[*]._from)
    LET phenotypeLookup = ${verbose
      ? `(FOR phenotype IN ${ontologyCollectionName} FILTER phenotype._id IN phenotypeIDs RETURN { [phenotype._id]: { phenotype_id: phenotype._id, phenotype_name: phenotype.name } })`
      : '[]'}
    LET elementLookup = ${verbose
      ? `(FOR element IN ${genomicElementCollectionName} FILTER element._id IN elementIDs RETURN { [element._id]: {${getDBReturnStatements(genomicElementSchema).replaceAll('record', 'element')}} })`
      : '[]'}
    LET phenotypeMap = MERGE(phenotypeLookup)
    LET elementMap = MERGE(elementLookup)
    FOR record IN edgeRecords
      RETURN {
        'phenotype': ${verbose ? 'phenotypeMap[record._to]' : 'record._to'},
        'genomic_element': ${verbose ? 'elementMap[record._from]' : 'record._from'},
        'name': record.name,
        'class': record.class,
        'label': record.label,
        'method': record.method,
        'source': record.source,
        'source_url': record.source_url,
        'files_filesets': record.files_filesets,
        'biological_context': record.biological_context,
        'biosample_term': record.biosample_term,
        'crispr_modality': record.crispr_modality,
        'z_score': record.z_score,
        'p_value': record.p_value,
        'neg_log10_pvalue': record.neg_log10_pvalue,
        'significant': record.significant,
        'num_guides': record.num_guides,
        'hit_guide_count': record.hit_guide_count,
        'nonhit_guide_count': record.nonhit_guide_count,
        'fraction_hit': record.fraction_hit
      }
  `
}

async function findPhenotypesFromGenomicElements (input: paramsFormatType): Promise<any[]> {
  validateQuery(input, ['region', 'files_fileset', 'method', 'phenotype_id'])
  delete input.organism
  const limit = applyLimit(input)
  const page = input.page as number
  delete input.page
  const verbose = input.verbose === 'true'
  delete input.verbose

  const edgeFilter = buildEdgeFilter(input)
  const elementFilter = getFilterStatements(genomicElementSchema, preProcessRegionParam(input))
  const elementClause = elementFilter !== ''
    ? `record._from IN (FOR element IN ${genomicElementCollectionName} FILTER ${elementFilter} RETURN element._id)`
    : ''
  const combinedFilter = [elementClause, edgeFilter].filter(filter => filter !== '').join(' AND ') || 'true'

  return await (await db.query(buildQuery({ combinedFilter, page, limit, verbose }))).all()
}

async function findGenomicElementsFromPhenotypes (input: paramsFormatType): Promise<any[]> {
  validateQuery(input, ['phenotype_id', 'phenotype_name', 'files_fileset', 'method'])
  delete input.organism
  const limit = applyLimit(input)
  const page = input.page as number
  delete input.page
  const verbose = input.verbose === 'true'
  delete input.verbose

  const phenotypeIds = await resolvePhenotypeIds(input)
  const edgeFilter = buildEdgeFilter(input)
  const phenotypeFilter = phenotypeIds.length > 0 ? `record._to IN ${JSON.stringify(phenotypeIds)}` : ''
  const combinedFilter = [phenotypeFilter, edgeFilter].filter(filter => filter !== '').join(' AND ') || 'true'

  return await (await db.query(buildQuery({ combinedFilter, page, limit, verbose }))).all()
}

const phenotypesFromGenomicElements = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genomic-elements/phenotypes', description: descriptions.genomic_elements_phenotypes } })
  .input(genomicElementQueryFormat)
  .output(outputFormat)
  .query(async ({ input }) => await findPhenotypesFromGenomicElements(input))

const genomicElementsFromPhenotypes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/phenotypes/genomic-elements', description: descriptions.phenotypes_genomic_elements } })
  .input(phenotypeQueryFormat)
  .output(outputFormat)
  .query(async ({ input }) => await findGenomicElementsFromPhenotypes(input))

export const genomicElementsPhenotypesRouters = {
  phenotypesFromGenomicElements,
  genomicElementsFromPhenotypes
}
