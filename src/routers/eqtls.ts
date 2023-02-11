import { z } from 'zod'
import { db } from '../database'
import { publicProcedure } from '../trpc'
import { TRPCError } from '@trpc/server'

export const eqtlsQueryFormat = z.object({
  geneId: z.string().optional(),
  biologicalContext: z.string().optional(),
  pValue: z.number().optional(),
  beta: z.number().optional(),
  page: z.number().optional()
})

export const eqtlsFormat = z.object({
  variant_id: z.string(),
  gene_id: z.string(),
  chr: z.string(),
  p_value: z.number(),
  beta: z.number(),
  slope: z.number(),
  biological_context: z.string()
})

export async function getQtls (
  geneId: string | undefined | null,
  biologicalContext: string | undefined | null,
  pValue: number | undefined | null,
  beta: number | undefined | null,
  page: number | undefined | null
): Promise<any[]> {
  const collection = 'variant_gene_links'

  const queryLimit = 25
  let queryPage = 0
  if (page != null && typeof page !== 'undefined') {
    queryPage = page
  }

  const filterBy = []

  if (geneId != null && typeof geneId !== 'undefined') {
    filterBy.push(`link._to == 'genes/${geneId}'`)
  }

  if (biologicalContext != null && typeof biologicalContext !== 'undefined') {
    filterBy.push(`link.biological_context == '${biologicalContext}'`)
  }

  if (filterBy.length === 0) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Either a gene ID or a biological context must be provided.'
    })
  }

  if (pValue != null && typeof pValue !== 'undefined') {
    filterBy.push(`link['p-value:long'] <= ${pValue}`)
  }

  if (beta != null && typeof beta !== 'undefined') {
    filterBy.push(`link['beta:long'] <= ${beta}`)
  }

  const filter = filterBy.join(' and ')

  const query = `
    FOR link IN ${collection}
    FILTER ${filter}
    LIMIT ${queryPage}, ${queryLimit}
    RETURN { variant_id: link.variant_id,
      gene_id: link.gene_id,
      chr: link.chr,
      p_value: link['p-value:long'],
      beta: link['beta:long'],
      slope: link['slope:long'],
      biological_context: link.biological_context
    }
  `
  const cursor = await db.query(query)

  const values = await cursor.all()
  return values
}

const endpointDescription = "Retrieve eQTL data for a given gene ID and biological context for P and Beta values lesser than given values. Example: gene ID = ENSG00000225972.1, biological context = 'brain amigdala', p value < 0.05, beta < 0.004"

export const eqtls = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/eqtls', description: endpointDescription } })
  .input(eqtlsQueryFormat)
  .output(z.array(eqtlsFormat))
  .query(async ({ input }) => await getQtls(input.geneId, input.biologicalContext, input.pValue, input.beta, input.page))
