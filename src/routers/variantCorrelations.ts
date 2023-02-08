import { aql } from 'arangojs'
import { z } from 'zod'
import { db } from '../database'
import { ancestryGroups } from '../constants'
import { publicProcedure } from '../trpc'

export const variantCorrelationQueryFormat = z.object({
  rsid: z.string(),
  ancestry: z.enum(ancestryGroups),
  page: z.number().optional()
})

export const variantCorrelationFormat = z.object({
  source: z.string(),
  target: z.string(),
  chr: z.string(),
  ancestry: z.string(),
  negated: z.string(),
  variant_1_base_pair: z.string(),
  variant_2_base_pair: z.string(),
  r2: z.number()
})

export async function getVariantCorrelations (rsid: string, ancestry: string, page: number | undefined | null): Promise<any[]> {
  const collection = db.collection('variant_correlations')

  const queryLimit = 100
  let queryPage = 0
  if (page != null && typeof page !== 'undefined') {
    queryPage = page
  }

  const snp = `snps/${rsid}`

  const query = aql`
    FOR correlation IN ${collection}
    FILTER (correlation._from == ${snp} or correlation._to == ${snp}) and correlation['r2:long'] <= 0.8 and correlation.ancestry == ${ancestry}
    LIMIT ${queryPage}, ${queryLimit}
    RETURN { source: correlation.source,
      target: correlation.target,
      chr: correlation.chr,
      ancestry: correlation.ancestry,
      negated: correlation['negated:boolean'],
      variant_1_base_pair: correlation.variant_1_base_pair,
      variant_2_base_pair: correlation.variant_2_base_pair,
      r2: correlation['r2:long']
    }
  `
  const cursor = await db.query(query)

  const values = await cursor.all()
  return values
}

const endpointDescription = 'Retrieve LD data for a given rsid from a certain ancestry with r2 < .8. Example: rsid = 10511349 and ancestry = SAS'

export const variantCorrelations = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variant-correlations/{rsid}', description: endpointDescription } })
  .input(variantCorrelationQueryFormat)
  .output(z.array(variantCorrelationFormat))
  .query(async ({ input }) => await getVariantCorrelations(input.rsid, input.ancestry, input.page))
