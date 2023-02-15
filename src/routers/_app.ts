import { router } from '../trpc'

import { regions } from './regionSearch'
import { variantCorrelations } from './variantCorrelations'
import { eqtls } from './eqtls'

export const appRouter = router({
  regions,
  variantCorrelations,
  eqtls
})

export type igvfCatalogRouter = typeof appRouter
