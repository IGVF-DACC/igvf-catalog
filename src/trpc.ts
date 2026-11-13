import { inferAsyncReturnType, initTRPC } from '@trpc/server'
import * as trpcExpress from '@trpc/server/adapters/express'
import { v4 as uuid } from 'uuid'
import { OpenApiMeta } from 'trpc-to-openapi'

export interface Context { requestId: string }
export const createContext = async ({ res }: trpcExpress.CreateExpressContextOptions): Promise<Context> => {
  const requestId = uuid()
  res.setHeader('x-request-id', requestId)
  res.setHeader('Cache-Control', 'max-age=86400') // 1 day
  return { requestId }
}
type defaultContext = inferAsyncReturnType<typeof createContext>

const t = initTRPC.context<defaultContext>().meta<OpenApiMeta>().create({
  // tRPC v11's default error shape always includes `data.path` (the internal procedure name,
  // e.g. "genesGenes") and, outside production, `data.stack` - both of which trpc-to-openapi's
  // HTTP adapter spreads straight into the JSON error response. The old trpc-openapi never did
  // this (it only ever sent { message, code, issues }), so this is new exposure introduced by
  // the library swap, not a deliberate choice - drop `data` to restore that minimal shape.
  errorFormatter ({ shape }) {
    const { data, ...rest } = shape
    return rest
  }
})

export const router = t.router
export const publicProcedure = t.procedure
