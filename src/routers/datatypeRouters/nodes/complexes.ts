import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFuzzy } from '../../genericRouters/routerFuzzy'
import { paramsFormatType } from '../_helpers'
import { TRPCError } from '@trpc/server'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

export const complexQueryFormat = z.object({
  complex_id: z.string().trim().optional(),
  name: z.string().trim().optional(),
  description: z.string().trim().optional(),
  page: z.number().default(0)
})

export const complexFormat = z.object({
  _id: z.string(),
  complex_name: z.string(),
  alias: z.array(z.string()).nullable(),
  molecules: z.array(z.string()).nullable(),
  evidence_code: z.string().nullable(),
  experimental_evidence: z.string().nullable(),
  description: z.string().nullable(),
  complex_assembly: z.string().or(z.array(z.string())).nullable(),
  complex_source: z.string().nullable(),
  reactome_xref: z.array(z.string()).nullable(),
  source: z.string(),
  source_url: z.string()
})

const schemaObj = schema.complex
const routerID = new RouterFilterByID(schemaObj)
const routerSearch = new RouterFuzzy(schemaObj)

export async function complexConditionalSearch (input: paramsFormatType): Promise<any[]> {
  if (input.complex_id !== undefined) {
    return await routerID.getObjectById(input.complex_id as string)
  }

  const searcheable: Record<string, string> = {}
  if (input.name !== undefined) {
    searcheable.complex_name = input.name as string
  }
  if (input.description !== undefined) {
    searcheable.description = input.description as string
  }

  if (searcheable) {
    return await routerSearch.textSearch(searcheable, 'token', input.page as number)
  }

  throw new TRPCError({
    code: 'BAD_REQUEST',
    message: 'At least one parameter must be defined.'
  })
}

export const complexes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/complexes', description: descriptions.complex } })
  .input(complexQueryFormat)
  .output(z.array(complexFormat).or(complexFormat))
  .query(async ({ input }) => await complexConditionalSearch(input))

export const complexesRouters = {
  complexes
}
