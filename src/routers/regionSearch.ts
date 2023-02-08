import { aql } from 'arangojs'
import { z } from 'zod'
import { db } from '../database'
import { publicProcedure } from '../trpc'
import { chrEnum } from '../constants'

export const regionQueryFormat = z.object({
  chr: z.enum(chrEnum),
  gte: z.number().int(),
  lt: z.number().int()
})

export const regionFormat = z.object({
  _key: z.string(),
  _id: z.string(),
  coordinates: z.object({ gte: z.number(), lt: z.number() }),
  strand: z.string(),
  value: z.string().nullish(),
  uuid: z.string()
})

export async function getRegions (gte: number, lt: number, chr: string): Promise<any[]> {
  const collection = db.collection('regions_chr' + chr)

  const query = aql`
    FOR peak IN ${collection}
    FILTER peak.coordinates.gte >= ${gte} and peak.coordinates.lt <= ${lt}
    RETURN peak
  `

  const cursor = await db.query(query)

  return await cursor.all()
}

export const regions = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/regions/{chr}' } })
  .input(regionQueryFormat)
  .output(z.array(regionFormat))
  .query(async ({ input }) => await getRegions(input.gte, input.lt, input.chr))
