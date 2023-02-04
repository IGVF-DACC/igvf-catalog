import { aql } from 'arangojs'
import { z } from 'zod'
import { db } from '../database'
import { publicProcedure } from '../trpc'

export const snpCorrelationQueryFormat = z.object({
  rsid: z.string(),
  page: z.number().optional()
})

export const snpCorrelationFormat = z.object({
  source: z.string(),
  target: z.string(),
  chr: z.string(),
  ancestry: z.string(),
  negated: z.string(),
  snp_1_base_pair: z.string(),
  snp_2_base_pair: z.string(),
  r2: z.number()
})

export async function getSnpCorrelations (rsid: string, page: number | undefined | null): Promise<any[]> {
  const collection = db.collection('snp_correlations')

  const queryLimit = 100
  let queryPage = 0
  if (page != null && typeof page !== 'undefined') {
    queryPage = page
  }

  const snp = `snps/${rsid}`

  const query = aql`
    FOR correlation IN ${collection}
    FILTER (correlation._from == ${snp} or correlation._to == ${snp}) and correlation['r2:long'] <= 0.8
    LIMIT ${queryPage}, ${queryLimit}
    RETURN { source: correlation.source,
      target: correlation.target,
      chr: correlation.chr,
      ancestry: correlation.ancestry,
      negated: correlation['negated:boolean'],
      snp_1_base_pair: correlation.snp_1_base_pair,
      snp_2_base_pair: correlation.snp_2_base_pair,
      r2: correlation['r2:long']
    }
  `
  const cursor = await db.query(query)

  const values = await cursor.all()

  return values
}

const endpointDescription = 'Retrieve LD data for a given rsid with r2 < .8 in ethnicity SAS. Example: rsid = 10511349'

export const snpCorrelations = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/snp-correlations/{rsid}', description: endpointDescription } })
  .input(snpCorrelationQueryFormat)
  .output(z.array(snpCorrelationFormat))
  .query(async ({ input }) => await getSnpCorrelations(input.rsid, input.page))
