import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { proteinFormat } from '../nodes/proteins'
import { descriptions } from '../descriptions'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { commonEdgeParamsFormat, proteinsCommonQueryFormat } from '../params'
import { getCollectionEnumValuesOrThrow, getEnumValuesOrThrow, getSchema } from '../schema'
import { TRPCError } from '@trpc/server'

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
  associated_protein_id: z.string().trim().optional(),
  associated_protein_name: z.string().trim().optional(),
  associated_uniprot_name: z.string().trim().optional(),
  associated_uniprot_full_name: z.string().trim().optional(),
  associated_dbxrefs: z.string().trim().optional(),
  pmid: z.string().trim().optional(),
  detection_method: detectionMethods.optional(),
  interaction_type: z.enum(INTERACTION_TYPES).optional(),
  label: labels.optional(),
  method: methods.optional(),
  source: sources.optional()
})).merge(commonEdgeParamsFormat)

const proteinsProteinsFormat = z.object({
  _id: z.string(),
  protein_1: z.string().or(z.array(proteinFormat.omit({ dbxrefs: true }))),
  protein_2: z.string().or(z.array(proteinFormat.omit({ dbxrefs: true }))),
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

function validateInput (input: paramsFormatType): void {
  const isInvalidProteinFilter = Object.keys(input).every(item => !['protein_id', 'protein_name', 'uniprot_name', 'uniprot_id', 'uniprot_full_name', 'dbxrefs', 'pmid'].includes(item))
  const isInvalidAssociatedProteinFilter = Object.keys(input).every(item => !['associated_protein_id', 'associated_uniprot_name', 'associated_uniprot_full_name', 'associated_protein_name', 'associated_dbxrefs'].includes(item))

  if (isInvalidProteinFilter && isInvalidAssociatedProteinFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one protein must be defined.'
    })
  }
}

async function proteinProteinSearch (input: paramsFormatType): Promise<any[]> {
  validateInput(input)

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

  const proteinInput: paramsFormatType = {
    _key: input.protein_id,
    name: input.protein_name,
    uniprot_names: input.uniprot_name,
    uniprot_full_names: input.uniprot_full_name,
    dbxrefs: input.dbxrefs
  }
  delete input.protein_id
  delete input.protein_name
  delete input.uniprot_name
  delete input.uniprot_full_name
  delete input.dbxrefs

  const associatedProteinInput: paramsFormatType = {
    _key: input.associated_protein_id,
    name: input.associated_protein_name,
    uniprot_names: input.associated_uniprot_name,
    uniprot_full_names: input.associated_uniprot_full_name,
    dbxrefs: input.associated_dbxrefs
  }
  delete input.associated_protein_id
  delete input.associated_protein_name
  delete input.associated_uniprot_name
  delete input.associated_uniprot_full_name
  delete input.associated_dbxrefs

  const filters = []

  if (input.source !== undefined) {
    if (input.source === 'IntAct' || input.source === 'BioGRID') {
      filters.push(`(record.source == "${input.source as string}" OR record.source == "BioGRID; IntAct")`)
    } else {
      filters.push(`record.source == "${input.source as string}"`)
    }
    delete input.source
  }

  let protein = getFilterStatements(proteinSchema, proteinInput).replaceAll('record', 'protein')
  let associatedProtein = getFilterStatements(proteinSchema, associatedProteinInput).replaceAll('record', 'associatedProtein')
  const edgeFilters = getFilterStatements(proteinProteinSchema, input)

  if (protein) {
    if (proteinInput._key !== undefined) {
      const proteinId = decodeURIComponent(proteinInput._key as string)
      protein = `protein._key == '${proteinId}' OR
            protein.protein_id == '${proteinId}' OR
            '${proteinId}' IN protein.uniprot_ids`
    }

    filters.push('(record._from == protein._id OR record._to == protein._id)')
  }

  if (associatedProtein) {
    if (associatedProteinInput._key !== undefined) {
      const associatedProteinId = decodeURIComponent(associatedProteinInput._key as string)
      associatedProtein = `associatedProtein._key == '${associatedProteinId}' OR
            associatedProtein.protein_id == '${associatedProteinId}' OR
            '${associatedProteinId}' IN associatedProtein.uniprot_ids`
    }

    filters.push('(record._from == associatedProtein._id OR record._to == associatedProtein._id)')
  }

  if (edgeFilters) {
    filters.push(edgeFilters)
  }

  const combinedFilter = filters.filter((filter) => filter !== '').join(' AND ')

  const query = `
    ${(protein)
      ? `FOR protein IN ${proteinCollectionName}
        FILTER ${protein}`
    : ''}

    ${(associatedProtein)
      ? `FOR associatedProtein IN ${proteinCollectionName}
        FILTER ${associatedProtein}`
      : ''}

    FOR record IN proteins_proteins
      FILTER ${combinedFilter}
      SORT record._key
      LIMIT ${page * limit}, ${limit}
      RETURN {
        '_id': record._id,
        'protein_1': ${verbose ? `(${sourceVerboseQuery})` : 'record._from'},
        'protein_2': ${verbose ? `(${targetVerboseQuery})` : 'record._to'},
        ${getDBReturnStatements(proteinProteinSchema)},
        'name': record.name
      }
    `

  return await (await db.query(query)).all()
}

const proteinsProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/proteins', description: descriptions.proteins_proteins } })
  .input(proteinsProteinsQueryFormat)
  .output(z.array(proteinsProteinsFormat))
  .query(async ({ input }) => await proteinProteinSearch(input))

export const proteinsProteinsRouters = {
  proteinsProteins
}
