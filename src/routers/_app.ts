import { router } from '../trpc'

import { nodeRouters } from './datatypeRouters/nodes/_all'

export const appRouter = router({ ...nodeRouters })

export type igvfCatalogRouter = typeof appRouter
