import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { geneFormat, geneSearch } from '../nodes/genes'
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
    z_score: z.string().trim().optional(),
    interaction_type: interactionTypes.optional(),
    label: z.enum(labels).optional(),
    method: z.enum(methodsEnum).optional(),
    source: z.enum(sources).optional(),
    name: z.enum(names).optional()
  })
).merge(commonEdgeParamsFormat)

const genesGenesRelativeFormat = z.object({
  'gene 1': z.string().or(z.array(geneFormat.omit({ synonyms: true }))),
  'gene 2': z.string().or(z.array(geneFormat.omit({ synonyms: true }))),
  z_score: z.number().optional(),
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
  name: z.string()
})

function validateInput (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['gene_id', 'hgnc_id', 'gene_name', 'alias'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one gene property must be defined.'
    })
  }
}

async function findGenesGenes (input: paramsFormatType): Promise<any[]> {
  validateInput(input)

  let genesSchema = HumangenesSchema
  let genesGenesSchema = HumangenesGenesSchema
  if (input.organism === 'Mus musculus') {
    genesSchema = MousegenesSchema
    genesGenesSchema = MousegenesGenesSchema
  }
  const genesCollectionName = genesSchema.db_collection_name as string
  const genesGenesCollectionName = genesGenesSchema.db_collection_name as string
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { gene_id, hgnc_id, gene_name: name, alias, organism } = input
  const geneInput: paramsFormatType = { gene_id, hgnc_id, name, alias, organism, page: 0 }
  delete input.gene_id
  delete input.hgnc_id
  delete input.gene_name
  delete input.alias
  delete input.organism
  const genes = await geneSearch(geneInput)
  const geneIDs = genes.map(gene => `${genesCollectionName}/${gene._id as string}`)

  const verbose = input.verbose === 'true'

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filters = getFilterStatements(genesGenesSchema, input)
  if (filters) {
    filters = ` AND ${filters}`
  }

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
      FOR record IN ${genesGenesCollectionName}
      FILTER (record._from IN ['${geneIDs.join('\', \'')}'] OR record._to IN ['${geneIDs.join('\', \'')}']) ${filters}
      SORT record._key
      LIMIT ${Number(input.page) * limit}, ${limit}
      RETURN MERGE({
        'name': record.name,
        'gene 1': ${verbose ? `(${sourceVerboseQuery})` : 'record._from'},
        'gene 2': ${verbose ? `(${targetVerboseQuery})` : 'record._to'}},
        (record.source == 'COXPRESdb' ? {${getDBReturnStatements(CoXPresdbSchema)}} : {${getDBReturnStatements(genesGenesSchema)}}))
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
