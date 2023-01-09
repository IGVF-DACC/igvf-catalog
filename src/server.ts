import { initTRPC } from '@trpc/server'
import { createHTTPServer } from '@trpc/server/adapters/standalone'
import { Database, aql } from 'arangojs'
import { z } from 'zod'

export type AppRouter = typeof appRouter

const chrEnum = [
  '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
  '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
  '21', '22', 'x', 'y'
] as const

async function getRegionsHandler (gte: number, lt: number, chr: string): Promise<any[]> {
  const db = new Database({
    url: 'http://127.0.0.1:8529/',
    databaseName: 'igvf',
    auth: { username: 'pedro', password: 'pedro' }
  })

  const collection = db.collection('regulome_chr' + chr)

  const query = aql`FOR peak IN ${collection}
  FILTER peak.coordinates.gte >= ${gte} and peak.coordinates.lt <= ${lt}
  RETURN peak`

  console.log(query)

  const cursor = await db.query(query)
  const result = await cursor.all()

  return result
}

const t = initTRPC.create()

const appRouter = t.router({
  regions: t.procedure
    .input(z.object({
      gte: z.number().int(),
      lt: z.number().int(),
      chr: z.enum(chrEnum)
    }))
    .query(async ({ input }) => await getRegionsHandler(input.gte, input.lt, input.chr))
})

export type igvfCatalogRouter = typeof appRouter

createHTTPServer({
  router: appRouter,
  createContext () {
    return {}
  }
}).listen(2023)
