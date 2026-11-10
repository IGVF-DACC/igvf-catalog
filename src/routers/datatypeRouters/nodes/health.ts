import { z } from 'zod/v4'
import { publicProcedure } from '../../../trpc'

// Health check response format
export const healthFormat = z.object({
  status: z.string()
})

// Health check endpoint
const health = publicProcedure
  .meta({
    openapi: {
      method: 'GET',
      path: '/health',
      description: 'Health check endpoint for the API service'
    }
  })
  .input(z.void())
  .output(healthFormat)
  .query(() => {
    return {
      status: 'ok'
    }
  })

export const healthRouters = {
  health
}
