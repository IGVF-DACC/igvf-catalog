import { Database, aql } from 'arangojs'
import { z } from 'zod'
import { envData } from './env'

const chrEnum = [
  '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
  '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
  '21', '22', 'x', 'y'
] as const

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
  const dbConfig = envData.database

  const db = new Database({
    url: dbConfig.connectionUri,
    databaseName: dbConfig.dbName,
    auth: {
      username: dbConfig.auth.username,
      password: dbConfig.auth.password
    }
  })

  const collection = db.collection('regulome_chr' + chr)

  const query = aql`
    FOR peak IN ${collection}
    FILTER peak.coordinates.gte >= ${gte} and peak.coordinates.lt <= ${lt}
    RETURN peak
  `

  const cursor = await db.query(query)

  return await cursor.all()
}
