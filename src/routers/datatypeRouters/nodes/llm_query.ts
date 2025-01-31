import { z } from 'zod'
import { llmQueryUrl } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'

const queryFormat = z.object({
  query: z.string()
})

const outputFormat = z.object({
  query: z.string(),
  result: z.string()

})

async function query (input: paramsFormatType): Promise<any> {
  const url = `${llmQueryUrl}query=${encodeURIComponent(input.query as string)}`
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
  return {
    query: input.query,
    result: jsonObj.result
  }
}

const llmQuery = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/llm-query', description: descriptions.genes } })
  .input(queryFormat)
  .output(outputFormat)
  .query(async ({ input }) => await query(input))

export const llmQueryRouters = {
  llmQuery
}
