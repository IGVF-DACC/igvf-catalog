import { router } from '../trpc'

import { genericRouters } from './genericRouters/genericRouters'

// Custom routers are meant for explicitly defined routers in compilation time
const customRouters = {}

export const appRouter = router({ ...genericRouters, ...customRouters })

export type igvfCatalogRouter = typeof appRouter
