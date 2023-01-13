import { aql } from 'arangojs'
import { z } from 'zod'
import { db } from '../database'
import { publicProcedure } from '../trpc'
import { chrEnum } from '../constants'

export const snpCorrelationQueryFormat = z.object({
  chr: z.enum(chrEnum),
  r: z.number().positive(),
  page: z.number().optional()
})

export const snpCorrelationFormat = z.object({
  _key: z.string(),
  _id: z.string(),
  _from: z.string(),
  _to: z.string(),
  _rev: z.string(),
  Uniq_ID_1: z.string(),
  Uniq_ID_2: z.string(),
  R2: z.number(),
  Dprime: z.number(),
  '+/-corr': z.number(),
  chrom: z.number()
})

export async function getSnpCorrelations (chr: string, r: number, page: number | undefined | null): Promise<any[]> {
  const collection = db.collection('topld')

  const queryLimit = 100
  let queryPage = 0
  if (page != null && typeof page !== 'undefined') {
    queryPage = page
  }

  const query = aql`
    FOR correlation IN ${collection}
    FILTER correlation.R2 >= ${r} and correlation.chrom == ${parseInt(chr)}
    LIMIT ${queryPage}, ${queryLimit}
    RETURN correlation
  `

  const cursor = await db.query(query)

  return await cursor.all()
}

export const snpCorrelations = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/snp-correlations/{chr}' } })
  .input(snpCorrelationQueryFormat)
  .output(z.array(snpCorrelationFormat))
  .query(async ({ input }) => await getSnpCorrelations(input.chr, input.r, input.page))
