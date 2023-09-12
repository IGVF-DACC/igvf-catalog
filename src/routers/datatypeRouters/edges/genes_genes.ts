import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'

const schema = loadSchemaConfig()

const schemaObj = schema['gene to gene coexpression association']

const routerEdge = new RouterEdges(schemaObj)

const genesGenesQueryFormat = z.object({
  gene_id: z.string(),
  source: z.enum(['CoXPresdb']).optional(),
  logit_score: z.string().optional(),
  page: z.number().default(0)
})

const genesGenesRelativeFormat = z.object({
  gene: z.any(),
  logit_score: z.string(),
  source: z.string(),
  source_url: z.string()
})

const genesGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/{gene_id}/genes' } })
  .input(genesGenesQueryFormat)
  .output(z.array(genesGenesRelativeFormat))
  .query(async ({ input }) => await routerEdge.getCompleteBidirectionalByID(input, 'gene_id', input.page, '_key'))

export const genesGenesEdgeRouters = {
  genesGenes
}
