import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { proteinFormat } from '../nodes/proteins'
import { descriptions } from '../descriptions'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { commonEdgeParamsFormat, proteinsCommonQueryFormat } from '../params'
import { getCollectionEnumValuesOrThrow, getEnumValuesOrThrow, getSchema } from '../schema'

const MAX_PAGE_SIZE = 250
const proteinProteinSchemaFile = 'data/schemas/edges/proteins_proteins.ProteinsInteraction.json'
const proteinProteinSchema = getSchema(proteinProteinSchemaFile)
const proteinSchema = getSchema('data/schemas/nodes/proteins.GencodeProtein.json')
const proteinCollectionName = proteinSchema.db_collection_name as string

const sources = z.enum(getEnumValuesOrThrow(proteinProteinSchemaFile, 'source'))
const detectionMethods = z.enum(getEnumValuesOrThrow(proteinProteinSchemaFile, 'detection_method'))
const methods = z.enum(getEnumValuesOrThrow(proteinProteinSchemaFile, 'method'))
const labels = z.enum(getEnumValuesOrThrow(proteinProteinSchemaFile, 'label'))

const INTERACTION_TYPES = getCollectionEnumValuesOrThrow('edges', 'proteins_proteins', 'interaction_type')

const proteinsProteinsQueryFormat = proteinsCommonQueryFormat.merge(z.object({
  pmid: z.string().trim().optional(),
  detection_method: detectionMethods.optional(),
  interaction_type: z.enum(INTERACTION_TYPES).optional(),
  label: labels.optional(),
  method: methods.optional(),
  source: sources.optional()
})).merge(commonEdgeParamsFormat)

const proteinsProteinsFormat = z.object({
  // ignore dbxrefs field to avoid long output
  'protein 1': z.string().or(z.array(proteinFormat.omit({ dbxrefs: true }))),
  'protein 2': z.string().or(z.array(proteinFormat.omit({ dbxrefs: true }))),
  detection_method: z.string(),
  detection_method_code: z.string(),
  interaction_type: z.array(z.enum(INTERACTION_TYPES)),
  interaction_type_code: z.array(z.string()),
  confidence_value_biogrid: z.number().nullable(),
  confidence_value_intact: z.number().nullable(),
  label: z.string(),
  class: z.string(),
  method: z.string(),
  source_url: z.string(),
  source: z.string(),
  organism: z.string(),
  pmids: z.array(z.string()),
  name: z.string()
})

async function proteinProteinSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const page = input.page as number
  const verbose = input.verbose === 'true'
  delete input.page
  delete input.verbose

  if (input.pmid !== undefined && input.pmid !== '') {
    const pmidUrl = 'http://pubmed.ncbi.nlm.nih.gov/'
    input.pmids = pmidUrl + (input.pmid as string)
    delete input.pmid
  }

  const sourceVerboseQuery = `
    FOR otherRecord IN ${proteinCollectionName}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(proteinSchema).replaceAll('record', 'otherRecord')}}
  `
  const targetVerboseQuery = `
    FOR otherRecord IN ${proteinCollectionName}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(proteinSchema).replaceAll('record', 'otherRecord')}}
  `

  const hasProteinQuery = input.protein_id !== undefined ||
    input.protein_name !== undefined ||
    input.uniprot_name !== undefined ||
    input.uniprot_full_name !== undefined ||
    input.dbxrefs !== undefined

  let proteinIdsQuery = ''
  let proteinIds: string[] = []
  if (hasProteinQuery) {
    if (input.protein_id !== undefined) {
      proteinIdsQuery = `
        FOR protein IN ${proteinCollectionName}
        FILTER protein._key == '${decodeURIComponent(input.protein_id as string)}' OR
                protein.protein_id == '${decodeURIComponent(input.protein_id as string)}' OR
                '${decodeURIComponent(input.protein_id as string)}' IN protein.uniprot_ids
        RETURN protein._id
      `
    } else {
      // eslint-disable-next-line @typescript-eslint/naming-convention
      const proteinInput: paramsFormatType = (({ protein_name, uniprot_name, uniprot_full_name, dbxrefs }) => ({ name: protein_name, uniprot_names: uniprot_name, uniprot_full_names: uniprot_full_name, dbxrefs }))(input)
      const proteinFilters = getFilterStatements(proteinSchema, proteinInput)
      proteinIdsQuery = `
        FOR record IN ${proteinCollectionName}
        FILTER ${proteinFilters}
        RETURN record._id
      `
    }
    delete input.protein_id
    delete input.protein_name
    delete input.uniprot_name
    delete input.uniprot_full_name
    delete input.dbxrefs

    proteinIds = await (await db.query(proteinIdsQuery)).all()
    if (proteinIds.length === 0) {
      return []
    }
  }

  const edgeFilters = getFilterStatements(proteinProteinSchema, input)
  const proteinFilter = hasProteinQuery ? '(record._from IN @proteinIds OR record._to IN @proteinIds)' : ''
  const combinedFilter = [proteinFilter, edgeFilters].filter((filter) => filter !== '').join(' AND ') || 'true'
  const filters = `FILTER ${combinedFilter}`
  const query = `
    FOR record IN proteins_proteins
      ${filters}
      SORT record._key
      LIMIT ${page * limit}, ${limit}
      RETURN {
        'protein 1': ${verbose ? `(${sourceVerboseQuery})` : 'record._from'},
        'protein 2': ${verbose ? `(${targetVerboseQuery})` : 'record._to'},
        ${getDBReturnStatements(proteinProteinSchema)},
        'name': record.name
      }
    `
  let result = []
  if (hasProteinQuery) {
    result = await (await db.query(query, { proteinIds })).all()
  } else {
    result = await (await db.query(query)).all()
  }
  return result
}

const proteinsProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/proteins', description: descriptions.proteins_proteins } })
  .input(proteinsProteinsQueryFormat)
  .output(z.array(proteinsProteinsFormat))
  .query(async ({ input }) => await proteinProteinSearch(input))

export const proteinsProteinsRouters = {
  proteinsProteins
}
