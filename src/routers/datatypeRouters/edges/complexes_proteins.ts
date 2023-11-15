import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { proteinFormat, proteinsQueryFormat } from '../nodes/proteins'
import { complexConditionalSearch, complexFormat, complexQueryFormat } from '../nodes/complexes'
import { paramsFormatType } from '../_helpers'

const proteinComplexFormat = z.object({
  source: z.string().optional(),
  source_url: z.string().optional(),
  protein: z.string().or(z.array(proteinFormat)).optional(),
  complex: z.string().or(z.array(complexFormat)).optional()
})

async function complexProteinConditionalSearch (input: paramsFormatType): Promise<any[]> {
  const verbose = input.verbose === 'true'

  delete input.verbose
  const complexes = await complexConditionalSearch(input)

  const complexIDs = complexes.map((c) => `complexes/${c._id as string}`)
  const complexFilter = `record._id IN ['${complexIDs.join('\',\'')}']`

  delete input.name
  delete input.description

  return await routerEdge.getTargets(input, '_key', verbose, complexFilter)
}

const schema = loadSchemaConfig()
const schemaObj = schema['complex to protein']
const routerEdge = new RouterEdges(schemaObj)

async function conditionalSearch (input: paramsFormatType): Promise<any[]> {
  if (input.complex_id !== undefined) {
    return await routerEdge.getTargetsByID(input.complex_id as string, input.page as number, '_key', input.verbose === 'true')
  }

  return await complexProteinConditionalSearch(input)
}

const proteinsFromComplexes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/complexes/proteins' } })
  .input(complexQueryFormat.merge(z.object({ verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(proteinComplexFormat))
  .query(async ({ input }) => await conditionalSearch(input))

const complexesFromProteinID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/{protein_id}/complexes' } })
  .input(z.object({ protein_id: z.string(), page: z.number().default(0), verbose: z.enum(['true', 'false']).default('false') }))
  .output(z.array(proteinComplexFormat))
  .query(async ({ input }) => await routerEdge.getSourcesByID(input.protein_id, input.page, 'chr', input.verbose === 'true'))

const complexesFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/complexes' } })
  .input(proteinsQueryFormat.merge(z.object({ verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(proteinComplexFormat))
  .query(async ({ input }) => await routerEdge.getSources(input, 'chr', input.verbose === 'true'))

export const complexesProteinsRouters = {
  proteinsFromComplexes,
  complexesFromProteins,
  complexesFromProteinID
}
