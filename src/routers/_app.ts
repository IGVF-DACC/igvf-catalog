import { router } from '../trpc'

import { regions } from './regionSearch'
import { variantCorrelations } from './variantCorrelations'

export const appRouter = router({
  regions,
  variantCorrelations
})

export type igvfCatalogRouter = typeof appRouter
