import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { envData } from '../../../env'

const TIMEOUT_MS = 120000 // 2 minutes

const queryFormat = z.object({
  query: z.string().max(5000),
  password: z.string(),
  verbose: z.enum(['true', 'false']).default('false')
})

const outputFormat = z.object({
  query: z.string(),
  aql: z.string().max(5000).optional(),
  aql_result: z.array(z.record(z.string(), z.any())).max(5).optional(),
  answer: z.string()
})

async function query (input: { query: string, password: string, verbose: string }): Promise<any> {
  const llmQueryUrl = envData.catalog_llm_query
  if (!input.query || typeof input.query !== 'string') {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Query must be a non-empty string'
    })
  }
  const controller = new AbortController()
  const timeout = setTimeout(() => {
    controller.abort()
  }, TIMEOUT_MS)

  try {
    const response = await fetch(llmQueryUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        password: input.password,
        query: input.query
      }),
      signal: controller.signal // Pass the abort signal to the fetch request
    })
    clearTimeout(timeout) // Clear the timeout if the request completes successfully
    const jsonObj = await response.json()

    if (!response.ok) {
      const errorMessage = jsonObj.error || 'The query could not be executed.'
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: errorMessage
      })
    }
    if (input.verbose === 'true') {
      return {
        query: input.query,
        aql: jsonObj.aql_query,
        aql_result: jsonObj.aql_result,
        answer: jsonObj.result
      }
    }
    return {
      query: input.query,
      answer: jsonObj.result
    }
  } catch (error: any) {
    if (error instanceof TRPCError) {
      throw error // Rethrow the TRPCError
    } else if (error.name === 'AbortError') {
      throw new TRPCError({
        code: 'TIMEOUT',
        message: 'The request timed out.'
      })
    } else {
      throw new TRPCError({
        code: 'INTERNAL_SERVER_ERROR',
        message: 'An unexpected error occurred.'
      })
    }
  }
}

const llmQuery = publicProcedure
  .meta({ openapi: { method: 'POST', path: '/llm-query', description: descriptions.llm_query } })
  .input(queryFormat)
  .output(outputFormat)
  .mutation(async ({ input }) => await query(input))

export const llmQueryRouters = {
  llmQuery
}
