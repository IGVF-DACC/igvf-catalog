import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonHumanEdgeParamsFormat } from '../params'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 500
const PHENOTYPE_NAMES = ['cell growth', 'cell migration'] as const

const genomicElementsPhenotypesSchema = getSchema('data/schemas/edges/genomic_elements_phenotypes.CRISPRElementPhenotype.json')
const genomicElementToPhenotypeCollectionName = 'genomic_elements_phenotypes'
const genomicElementSchema = getSchema('data/schemas/nodes/genomic_elements.CCRE.json')
const genomicElementCollectionName = genomicElementSchema.db_collection_name as string
const ontologyCollectionName = 'ontology_terms'

const edgeQueryFormat = z.object({
  files_fileset: z.string().optional(),
  phenotype_id: z.string().trim().optional(),
  phenotype_name: z.enum(PHENOTYPE_NAMES).optional(),
  // Omit or set to true: true returns only significant associations.
  significant: z.enum(['true']).optional()
})

const genomicElementQueryFormat = z.object({
  region: z.string().trim().optional()
}).merge(edgeQueryFormat).merge(commonHumanEdgeParamsFormat)

const phenotypeQueryFormat = edgeQueryFormat.merge(commonHumanEdgeParamsFormat)

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
  num_guides_hit: z.number().nullish(),
  num_guides_nonhit: z.number().nullish(),
  fraction_guides_hit: z.number().nullish(),
  phenotype_name: z.string().nullish(),
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
  if (input.significant === 'true') {
    input.significant = true
  } else {
    delete input.significant
  }

  const filters = getFilterStatements(genomicElementsPhenotypesSchema, input)
  delete input.files_filesets
  delete input.significant
  return filters
}

async function resolvePhenotypeIds (input: paramsFormatType): Promise<string[]> {
  const phenotypeName = input.phenotype_name as string | undefined
  delete input.phenotype_name

  if (input.phenotype_id !== undefined) {
    const phenotypeId = `ontology_terms/${input.phenotype_id as string}`
    delete input.phenotype_id
    return [phenotypeId]
  }

  if (phenotypeName === undefined) {
    return []
  }

  const phenotypes = await (await db.query(`
    FOR record IN ${ontologyCollectionName}
    FILTER record.name == @phenotypeName
    RETURN record._id
  `, { phenotypeName })).all()

  return phenotypes
}

const buildCombinedFilter = (...filters: string[]): string => {
  return filters.filter((filter) => filter !== '').join(' AND ') || 'true'
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
      LET phenotype_name = DOCUMENT(record._to).name
      RETURN {
        'phenotype': ${verbose ? 'phenotypeMap[record._to]' : 'record._to'},
        'phenotype_name': phenotype_name,
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
        'num_guides_hit': record.num_guides_hit,
        'num_guides_nonhit': record.num_guides_nonhit,
        'fraction_guides_hit': record.fraction_guides_hit
      }
  `
}

async function executePhenotypesQuery (
  combinedFilter: string,
  page: number,
  limit: number,
  verbose: boolean,
  bindVars?: Record<string, unknown>
): Promise<any[]> {
  const query = buildQuery({ combinedFilter, page, limit, verbose })
  return bindVars !== undefined
    ? await (await db.query(query, bindVars)).all()
    : await (await db.query(query)).all()
}

async function findPhenotypesFromGenomicElements (input: paramsFormatType): Promise<any[]> {
  validateQuery(input, ['region', 'files_fileset', 'phenotype_id', 'phenotype_name'])
  delete input.organism
  const limit = applyLimit(input)
  const page = input.page as number
  delete input.page
  const verbose = input.verbose === 'true'
  delete input.verbose

  let elementIDs: string[] = []
  let isElementQuery = false
  if (input.region !== undefined) {
    isElementQuery = true
    const elementInput: paramsFormatType = {
      region: input.region,
      page: 0
    }
    const genomicElementsFilters = getFilterStatements(genomicElementSchema, preProcessRegionParam(elementInput))
    const elementQuery = `
      FOR record IN ${genomicElementCollectionName}
      FILTER ${genomicElementsFilters}
      RETURN record._id
    `
    elementIDs = await (await db.query(elementQuery)).all()
    delete input.region
  }

  const phenotypeIds = await resolvePhenotypeIds(input)
  const edgeFilter = buildEdgeFilter(input)
  const elementFilter = isElementQuery ? 'record._from IN @elementIDs' : ''
  const phenotypeFilter = phenotypeIds.length > 0 ? `record._to IN ${JSON.stringify(phenotypeIds)}` : ''
  const combinedFilter = buildCombinedFilter(elementFilter, phenotypeFilter, edgeFilter)
  const bindVars = isElementQuery ? { elementIDs } : undefined

  return await executePhenotypesQuery(combinedFilter, page, limit, verbose, bindVars)
}

async function findGenomicElementsFromPhenotypes (input: paramsFormatType): Promise<any[]> {
  validateQuery(input, ['phenotype_id', 'phenotype_name', 'files_fileset'])
  delete input.organism
  const limit = applyLimit(input)
  const page = input.page as number
  delete input.page
  const verbose = input.verbose === 'true'
  delete input.verbose

  const phenotypeIds = await resolvePhenotypeIds(input)
  const edgeFilter = buildEdgeFilter(input)
  const phenotypeFilter = phenotypeIds.length > 0 ? `record._to IN ${JSON.stringify(phenotypeIds)}` : ''
  const combinedFilter = buildCombinedFilter(phenotypeFilter, edgeFilter)

  return await executePhenotypesQuery(combinedFilter, page, limit, verbose)
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
