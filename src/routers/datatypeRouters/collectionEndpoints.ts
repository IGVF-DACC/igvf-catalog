import { z } from 'zod'
import { publicProcedure } from '../../trpc'
import { descriptions } from './descriptions'
import { COLLECTION_ENDPOINTS, type CollectionType } from '../../collectionEndpoints'

const collectionEndpointsQueryFormat = z.object({
  collection: z.string().trim().optional(),
  type: z.enum(['node', 'edge']).optional()
})

const collectionEndpointFormat = z.object({
  collection: z.string(),
  type: z.enum(['node', 'edge']),
  endpoints: z.array(z.string())
})

interface CollectionEndpointsInput {
  collection?: string
  type?: CollectionType
}

// Returns the subset of COLLECTION_ENDPOINTS matching the given filters, in
// the same shape regardless of which (if any) filters are passed - callers
// that just want the whole mapping (e.g. to build their own lookup table
// once) can call this with no params at all.
function lookupCollectionEndpoints (input: CollectionEndpointsInput): Array<z.infer<typeof collectionEndpointFormat>> {
  return Object.entries(COLLECTION_ENDPOINTS)
    .filter(([collection]) => input.collection === undefined || collection === input.collection)
    .filter(([, { type }]) => input.type === undefined || type === input.type)
    .map(([collection, { type, endpoints }]) => ({ collection, type, endpoints }))
}

const collectionEndpoints = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/collection-endpoints', description: descriptions.collection_endpoints } })
  .input(collectionEndpointsQueryFormat)
  .output(z.array(collectionEndpointFormat))
  .query(async ({ input }) => lookupCollectionEndpoints(input))

export const collectionEndpointsRouters = {
  collectionEndpoints
}
