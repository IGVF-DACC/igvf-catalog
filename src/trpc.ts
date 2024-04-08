import { inferAsyncReturnType, initTRPC } from '@trpc/server'
import * as trpcExpress from '@trpc/server/adapters/express'
import { v4 as uuid } from 'uuid'
import { OpenApiMeta } from 'trpc-openapi'

export interface Context { requestId: string }
export const createContext = async ({ res }: trpcExpress.CreateExpressContextOptions): Promise<Context> => {
  const requestId = uuid()
  res.setHeader('x-request-id', requestId)
  res.setHeader('Cache-Control', 'max-age=86400') // 1 day
  return { requestId }
}
type defaultContext = inferAsyncReturnType<typeof createContext>

const t = initTRPC.context<defaultContext>().meta<OpenApiMeta>().create()

export const router = t.router
export const publicProcedure = t.procedure
