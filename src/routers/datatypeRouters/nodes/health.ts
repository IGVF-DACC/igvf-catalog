import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { db } from '../../../database'
import { envData } from '../../../env'

// Health check response format
export const healthFormat = z.object({
  status: z.string(),
  arangodb: z.string(),
  database_url: z.string()
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
  .query(async () => {
    let arangodbStatus = 'OK'
    let overallStatus = 'OK'

    try {
      // Test database connection with a simple query
      const cursor = await db.query('RETURN 1')
      await cursor.all()
    } catch (error) {
      arangodbStatus = `ERROR: ${error instanceof Error ? error.message : 'Unknown error'}`
      overallStatus = 'ERROR'
    }

    return {
      status: overallStatus,
      arangodb: arangodbStatus,
      database_url: envData.database.connectionUri
    }
  })

export const healthRouters = {
  health
}
