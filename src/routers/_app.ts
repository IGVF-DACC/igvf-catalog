import { router } from '../trpc'

import { nodeRouters } from './datatypeRouters/nodes/_all'
import { edgeRouters } from './datatypeRouters/edges/_all'

// Edge endpoints must preceed node endpoints to avoid naming conflicts
export const appRouter = router({ ...edgeRouters, ...nodeRouters })

export type igvfCatalogRouter = typeof appRouter
