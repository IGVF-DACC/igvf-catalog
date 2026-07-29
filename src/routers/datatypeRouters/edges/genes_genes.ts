import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { geneFormat } from '../nodes/genes'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { commonEdgeParamsFormat, genesCommonQueryFormat } from '../params'
import { getCollectionEnumValuesOrThrow, getSchema } from '../schema'

const MAX_PAGE_SIZE = 100

const HumangenesGenesSchema = getSchema('data/schemas/edges/genes_genes.GeneGeneBiogrid.json') // union of properties from coxpresdb & biogrid
const MousegenesGenesSchema = getSchema('data/schemas/edges/mm_genes_mm_genes.GeneGeneBiogrid.json')
const CoXPresdbSchema = getSchema('data/schemas/edges/genes_genes.Coxpresdb.json') // human coexpredb
const HumangenesSchema = getSchema('data/schemas/nodes/genes.GencodeGene.json')
const MousegenesSchema = getSchema('data/schemas/nodes/mm_genes.GencodeGene.json')

const interactionTypes = z.enum([
  'dosage growth defect (sensu BioGRID)',
  'dosage lethality (sensu BioGRID)',
  'dosage rescue (sensu BioGRID)',
  'negative genetic interaction (sensu BioGRID)',
  'phenotypic enhancement (sensu BioGRID)',
  'phenotypic suppression (sensu BioGRID)',
  'positive genetic interaction (sensu BioGRID)',
  'synthetic growth defect (sensu BioGRID)',
  'synthetic lethality (sensu BioGRID)',
  'synthetic rescue (sensu BioGRID)'
])
const sources = getCollectionEnumValuesOrThrow('edges', 'genes_genes', 'source')
const names = getCollectionEnumValuesOrThrow('edges', 'genes_genes', 'name')
const labels = getCollectionEnumValuesOrThrow('edges', 'genes_genes', 'label')
const methodsHuman = getCollectionEnumValuesOrThrow('edges', 'genes_genes', 'method')
const methodsMouse = getCollectionEnumValuesOrThrow('edges', 'mm_genes_mm_genes', 'method')
// need to combine methodsHuman and methodsMouse, remove duplicates and sort
const methods = [...methodsHuman, ...methodsMouse]
  .filter((value, index, self) => self.indexOf(value) === index)
  .sort((a, b) => a.localeCompare(b))
const methodsEnum = methods as [string, ...string[]]

const genesGenesQueryFormat = genesCommonQueryFormat.merge(
  z.object({
    associated_gene_id: z.string().trim().optional(),
    associated_hgnc_id: z.string().trim().optional(),
    associated_gene_name: z.string().trim().optional(),
    associated_alias: z.string().trim().optional(),
    z_score: z.string().trim().optional(),
    interaction_type: interactionTypes.optional(),
    label: z.enum(labels).optional(),
    method: z.enum(methodsEnum).optional(),
    source: z.enum(sources).optional(),
    name: z.enum(names).optional(),
    files_fileset: z.string().trim().optional()
  })
).merge(commonEdgeParamsFormat)

const genesGenesRelativeFormat = z.object({
  _id: z.string(),
  gene_1: z.string().or(z.array(geneFormat.omit({ synonyms: true }))),
  gene_2: z.string().or(z.array(geneFormat.omit({ synonyms: true }))),
  z_score: z.number().optional(),
  associated_process: z.string().nullish(),
  detection_method: z.string().optional(),
  detection_method_code: z.string().optional(),
  interaction_type: z.array(z.string()).optional(),
  interaction_type_code: z.array(z.string()).optional(),
  confidence_value_biogrid: z.number().nullable().optional(),
  confidence_value_intact: z.number().nullable().optional(),
  pmids: z.array(z.string()).optional(),
  label: z.string(),
  method: z.string(),
  class: z.string(),
  source: z.string(),
  source_url: z.string().optional(),
  name: z.string(),
  files_filesets: z.string().nullish()
})

function validateInput (input: paramsFormatType): void {
  const isInvalidGeneFilter = Object.keys(input).every(item => !['gene_id', 'hgnc_id', 'gene_name', 'alias'].includes(item))
  const isInvalidAssociatedGeneFilter = Object.keys(input).every(item => !['associated_gene_id', 'associated_hgnc_id', 'associated_gene_name', 'associated_alias'].includes(item))

  if (isInvalidGeneFilter && isInvalidAssociatedGeneFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one gene must be defined.'
    })
  }

  if (input.z_score !== undefined) {
    if (isNaN(Number(input.z_score)) && !(input.z_score as string).includes(':')) {
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: 'z_score must be a number or a string in the format of "operator:value", where operator can be one of "gt", "gte", "lt" or "lte".'
      })
    }
  }
}

async function findGenesGenes (input: paramsFormatType): Promise<any[]> {
  validateInput(input)

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let genesSchema = HumangenesSchema
  let genesGenesSchema = HumangenesGenesSchema
  if (input.organism === 'Mus musculus') {
    genesSchema = MousegenesSchema
    genesGenesSchema = MousegenesGenesSchema
  }
  delete input.organism

  if (input.files_fileset !== undefined) {
    input.files_filesets = `files_filesets/${input.files_fileset as string}`
    delete input.files_fileset
  }

  const genesCollectionName = genesSchema.db_collection_name as string
  const genesGenesCollectionName = genesGenesSchema.db_collection_name as string

  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { gene_id, hgnc_id, gene_name: name, alias } = input
  const geneInput: paramsFormatType = { _key: gene_id, hgnc_id, name, alias, page: 0 }
  delete input.gene_id
  delete input.hgnc_id
  delete input.gene_name
  delete input.alias

  const associatedGeneInput: paramsFormatType = {
    _key: input.associated_gene_id,
    hgnc_id: input.associated_hgnc_id,
    name: input.associated_gene_name,
    alias: input.associated_alias,
    page: 0
  }
  delete input.associated_gene_id
  delete input.associated_hgnc_id
  delete input.associated_gene_name
  delete input.associated_alias

  const filters = []
  const gene = getFilterStatements(genesSchema, geneInput).replaceAll('record', 'gene')
  const associatedGene = getFilterStatements(genesSchema, associatedGeneInput).replaceAll('record', 'associatedGene')
  const edgeFilters = getFilterStatements(genesGenesSchema, input)

  if (gene) {
    filters.push('(record._from == gene._id OR record._to == gene._id)')
  }

  if (associatedGene) {
    filters.push('(record._from == associatedGene._id OR record._to == associatedGene._id)')
  }

  if (edgeFilters) {
    filters.push(edgeFilters)
  }

  const combinedFilter = filters.filter((filter) => filter !== '').join(' AND ')

  const sourceVerboseQuery = `
  FOR otherRecord IN ${genesCollectionName}
  FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
  RETURN {${getDBReturnStatements(genesSchema).replaceAll('record', 'otherRecord')}}
`
  const targetVerboseQuery = `
    FOR otherRecord IN ${genesCollectionName}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(genesSchema).replaceAll('record', 'otherRecord')}}
  `

  const query = `
    ${(gene)
      ? `FOR gene IN ${genesCollectionName}
        FILTER ${gene}`
    : ''}

    ${(associatedGene)
      ? `FOR associatedGene IN ${genesCollectionName}
        FILTER ${associatedGene}`
      : ''}

    FOR record IN ${genesGenesCollectionName}
    FILTER ${combinedFilter}
    SORT record._key
    LIMIT ${Number(input.page) * limit}, ${limit}
    RETURN DISTINCT(MERGE({
      '_id': record._id,
      'name': record.name,
      'gene_1': ${input.verbose === 'true' ? `(${sourceVerboseQuery})` : 'record._from'},
      'gene_2': ${input.verbose === 'true' ? `(${targetVerboseQuery})` : 'record._to'}},
      (record.source == 'COXPRESdb' ? {${getDBReturnStatements(CoXPresdbSchema)}} : {${getDBReturnStatements(genesGenesSchema)}})))
  `

  return await (await db.query(query)).all()
}

const genesGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/genes', description: descriptions.genes_genes } })
  .input(genesGenesQueryFormat)
  .output(z.array(genesGenesRelativeFormat))
  .query(async ({ input }) => await findGenesGenes(input))

export const genesGenesEdgeRouters = {
  genesGenes
}
