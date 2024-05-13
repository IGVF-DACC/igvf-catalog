import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { geneFormat } from '../nodes/genes'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'

const MAX_PAGE_SIZE = 100

const schema = loadSchemaConfig()
const HumangenesGenesSchema = schema['gene to gene interaction'] // union of properties from coxpresdb & biogrid
const MousegenesGenesSchema = schema['mouse gene to gene interaction']
const HumangenesSchema = schema.gene
const MousegenesSchema = schema['gene mouse']

//change gene_name;
const genesGenesQueryFormat = z.object({
  gene_id: z.string().trim().optional(),
  gene_name: z.string().trim().optional(),
  organism: z.enum(['Mus musculus', 'Homo sapiens']).default('Homo sapiens'),
  source: z.enum(['CoXPresdb', 'BioGRID']).optional(),
  z_score: z.string().trim().optional(),
  page: z.number().default(0),
  verbose: z.enum(['true', 'false']).default('false')
})

const genesGenesRelativeFormat = z.object({
  'gene 1': z.string().or(z.array(geneFormat.omit({ alias: true }))),
  'gene 2': z.string().or(z.array(geneFormat.omit({ alias: true }))),
  z_score: z.number().optional(),
  detection_method: z.string().nullable(),
  detection_method_code: z.string().nullable(),
  interaction_type: z.array(z.string()).nullable(),
  interaction_type_code: z.array(z.string()).nullable(),
  confidence_value_biogrid: z.number().nullable(),
  confidence_value_intact: z.number().nullable(),
  pmids: z.array(z.string()).nullable(),
  source: z.string()
})

async function findGenesGenes (input: paramsFormatType): Promise<any[]> {
  const verbose = input.verbose === 'true'

  let genesSchema = HumangenesSchema
  let genesGenesSchema = HumangenesGenesSchema

  if (input.organism === 'Mus musculus') {
    genesSchema = MousegenesSchema
    genesGenesSchema = MousegenesGenesSchema
  }
  delete input.organism

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let geneFilters = ''

  if (input.gene_id !== undefined) {
    geneFilters = `record._id == '${genesSchema.db_collection_name as string}/${input.gene_id as string}'`
    delete input.gene_id
  } else {
    if (input.gene_name !== undefined) {
      geneFilters = `record.name == '${input.gene_name}'`
      delete input.gene_name
    } else {
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: 'At least one gene property needs to be defined.'
      })
    }
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
    LET geneNodes = (
      FOR record IN ${genesSchema.db_collection_name as string}
      FILTER ${geneFilters}
      RETURN record._id
    )

    FOR record IN ${genesGenesSchema.db_collection_name as string}
    FILTER (record._from IN geneNodes OR record._to IN geneNodes) ${filters}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN {
      'gene 1': ${verbose ? `(${sourceVerboseQuery})` : 'record._from'},
      'gene 2': ${verbose ? `(${targetVerboseQuery})` : 'record._to'},
      ${getDBReturnStatements(genesGenesSchema)}}
  `

  return await (await db.query(query)).all()
}

const genesGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/genes', description: descriptions.genes_genes } })
  .input(genesGenesQueryFormat.merge(z.object({ limit: z.number().optional() })))
  .output(z.array(genesGenesRelativeFormat))
  .query(async ({ input }) => await findGenesGenes(input))

export const genesGenesEdgeRouters = {
  genesGenes
}
