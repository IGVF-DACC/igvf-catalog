import { inferAsyncReturnType, initTRPC } from '@trpc/server'
import { OpenApiMeta } from 'trpc-openapi'
import { z } from 'zod'
import { getRegions, regionFormat, regionQueryFormat } from './database'
import * as trpcExpress from '@trpc/server/adapters/express'
import { v4 as uuid } from 'uuid'

export interface Context { requestId: string }
export const createContext = async ({ res }: trpcExpress.CreateExpressContextOptions): Promise<Context> => {
  const requestId = uuid()
  res.setHeader('x-request-id', requestId)
  return { requestId }
}
type defaultContext = inferAsyncReturnType<typeof createContext>

const t = initTRPC.context<defaultContext>().meta<OpenApiMeta>().create()

export const appRouter = t.router({
  regions: t.procedure
    .meta({ openapi: { method: 'GET', path: '/regions/{chr}' } })
    .input(regionQueryFormat)
    .output(z.array(regionFormat))
    .query(async ({ input }) => await getRegions(input.gte, input.lt, input.chr))
})

export type igvfCatalogRouter = typeof appRouter
