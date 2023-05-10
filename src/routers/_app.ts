import { router } from '../trpc'

import { genericRouters } from './genericRouters/genericRouters'
import { nodeRouters } from './datatypeRouters/nodes/_all'

export const appRouter = router({ ...genericRouters, ...nodeRouters })

export type igvfCatalogRouter = typeof appRouter
