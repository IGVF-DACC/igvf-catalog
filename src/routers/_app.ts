import { router } from '../trpc'

import { nodeRouters } from './datatypeRouters/nodes/_all'
import { edgeRouters } from './datatypeRouters/edges/_all'
import { summaryRouters } from './datatypeRouters/summaries/_all'
import { autocompleteRouters } from './datatypeRouters/autocomplete'

// Edge endpoints must preceed node endpoints to avoid naming conflicts
export const appRouter = router({
  ...autocompleteRouters,
  ...edgeRouters,
  ...nodeRouters,
  ...summaryRouters
})

export type igvfCatalogRouter = typeof appRouter
