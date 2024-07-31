import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { geneFormat, geneSearch } from '../nodes/genes'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { commonEdgeParamsFormat, genesCommonQueryFormat } from '../params'

const MAX_PAGE_SIZE = 100

const schema = loadSchemaConfig()
const HumangenesGenesSchema = schema['gene to gene interaction'] // union of properties from coxpresdb & biogrid
const MousegenesGenesSchema = schema['mouse gene to gene interaction']
const CoXPresdbSchema = schema['gene to gene coexpression association'] // human coexpredb
const HumangenesSchema = schema.gene
const MousegenesSchema = schema['gene mouse']

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

const genesGenesQueryFormat = genesCommonQueryFormat.merge(
  z.object({
    source: z.enum(['CoXPresdb', 'BioGRID']).optional(),
    'interaction type': interactionTypes.optional(),
    z_score: z.string().trim().optional()
  })
).merge(commonEdgeParamsFormat)

const genesGenesRelativeFormat = z.object({
  'gene 1': z.string().or(z.array(geneFormat.omit({ alias: true }))),
  'gene 2': z.string().or(z.array(geneFormat.omit({ alias: true }))),
  z_score: z.number().optional(),
  detection_method: z.string().optional(),
  detection_method_code: z.string().optional(),
  interaction_type: z.array(z.string()).optional(),
  interaction_type_code: z.array(z.string()).optional(),
  confidence_value_biogrid: z.number().nullable().optional(),
  confidence_value_intact: z.number().nullable().optional(),
  pmids: z.array(z.string()).optional(),
  source: z.string(),
  source_url: z.string().optional()
})

function validateInput (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['gene_id', 'hgnc', 'gene_name', 'alias'].includes(item))
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
  const { gene_id, hgnc, gene_name: name, region, alias, gene_type, organism, page } = input
  const geneInput: paramsFormatType = { gene_id, hgnc, name, region, alias, gene_type, organism, page }
  delete input.gene_id
  delete input.hgnc
  delete input.gene_name
  delete input.region
  delete input.alias
  delete input.gene_type
  delete input.organism
  const genes = await geneSearch(geneInput)
  const geneIDs = genes.map(gene => `${genesSchema.db_collection_name as string}/${gene._id as string}`)

  const verbose = input.verbose === 'true'

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let arrayFilters = ''
  if (input['interaction type'] !== undefined) {
    arrayFilters = `AND '${input['interaction type']}' IN record.interaction_type[*]`
    delete input['interaction type']
  }

  let filters = getFilterStatements(genesGenesSchema, input)
  if (filters) {
    filters = ` AND ${filters}`
  }

  const sourceVerboseQuery = `
  FOR otherRecord IN ${genesSchema.db_collection_name as string}
  FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
  RETURN {${getDBReturnStatements(genesSchema).replaceAll('record', 'otherRecord')}}
`
  const targetVerboseQuery = `
    FOR otherRecord IN ${genesSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(genesSchema).replaceAll('record', 'otherRecord')}}
  `

  const query = `
      FOR record IN ${genesGenesSchema.db_collection_name as string}
      FILTER (record._from IN ['${geneIDs.join('\', \'')}'] OR record._to IN ['${geneIDs.join('\', \'')}']) ${filters} ${arrayFilters}
      SORT record._key
      LIMIT ${Number(input.page) * limit}, ${limit}
      RETURN MERGE({
        'gene 1': ${verbose ? `(${sourceVerboseQuery})` : 'record._from'},
        'gene 2': ${verbose ? `(${targetVerboseQuery})` : 'record._to'}},
        (record.source == 'CoXPresdb' ? {${getDBReturnStatements(CoXPresdbSchema)}} : {${getDBReturnStatements(genesGenesSchema)}}))
    `.toString()
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
