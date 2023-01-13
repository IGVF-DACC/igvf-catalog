import { router } from '../trpc'

import { regions } from './regionSearch'
import { snpCorrelations } from './snpCorrelations'

export const appRouter = router({
  regions,
  snpCorrelations
})

export type igvfCatalogRouter = typeof appRouter
