import { z } from 'zod'
import { llmQueryUrl } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { envData } from '../../../env'

const queryFormat = z.object({
  query: z.string(),
  password: z.string(),
  verbose: z.enum(['true', 'false']).default('false')
})

const outputFormat = z.object({
  query: z.string(),
  aql: z.string().optional(),
  aql_result: z.array(z.record(z.string(), z.any())).optional(),
  answer: z.string()

})

async function query (input: { query: string, password: string, verbose: string }): Promise<any> {
  const correctPassword = envData.database.auth.password
  if (input.password !== correctPassword) {
    throw new TRPCError({
      code: 'UNAUTHORIZED',
      message: 'Invalid password'
    })
  }
  const url = `${llmQueryUrl}query=${encodeURIComponent(input.query)}`
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'The query could not be executed.'
    })
  }
  const jsonObj = await response.json()
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
}

const llmQuery = publicProcedure
  .meta({ openapi: { method: 'POST', path: '/llm-query', description: descriptions.llm_query } })
  .input(queryFormat)
  .output(outputFormat)
  .mutation(async ({ input }) => await query(input))

export const llmQueryRouters = {
  llmQuery
}
