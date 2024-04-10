import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { descriptions } from '../descriptions'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'

const MAX_PAGE_SIZE = 100

const schema = loadSchemaConfig()
const genesGenesSchema = schema['gene to gene coexpression association']

const genesGenesQueryFormat = z.object({
  gene_id: z.string().trim(),
  source: z.enum(['CoXPresdb']).optional(),
  logit_score: z.string().trim().optional(),
  page: z.number().default(0)
})

const genesGenesRelativeFormat = z.object({
  gene: z.any(),
  logit_score: z.number(),
  source: z.string(),
  source_url: z.string()
})

async function findGenesGenes (input: paramsFormatType): Promise<any[]> {
  const id = `genes/${decodeURIComponent(input.gene_id as string)}`
  delete input.gene_id

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filters = getFilterStatements(genesGenesSchema, input)
  if (filters) {
    filters = ` AND ${filters}`
  }

  const query = `
    FOR record IN ${genesGenesSchema.db_collection_name}
    FILTER (record._from == '${id}' OR record._to == '${id}') ${filters}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN {
      gene: UNSET(DOCUMENT(record._from == '${id}' ? record._to : record._from), '_rev', '_id'),
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
