import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { proteinFormat, proteinsQueryFormat } from '../nodes/proteins'
import { complexConditionalSearch, complexFormat, complexQueryFormat } from '../nodes/complexes'
import { paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'

const proteinComplexFormat = z.object({
  source: z.string().optional(),
  source_url: z.string().optional(),
  protein: z.string().or(z.array(proteinFormat)).optional(),
  complex: z.string().or(z.array(complexFormat)).optional()
})

const schema = loadSchemaConfig()
const schemaObj = schema['complex to protein']
const routerEdge = new RouterEdges(schemaObj)

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

async function conditionalProteinSearch (input: paramsFormatType): Promise<any[]> {
  if (input.protein_id !== undefined) {
    return await routerEdge.getSourcesByID(input.protein_id as string, input.page as number, 'chr', input.verbose === 'true')
  }

  return await routerEdge.getSources(input, 'chr', input.verbose === 'true')
}

async function conditionalSearch (input: paramsFormatType): Promise<any[]> {
  if (input.complex_id !== undefined) {
    return await routerEdge.getTargetsByID(input.complex_id as string, input.page as number, '_key', input.verbose === 'true')
  }

  return await complexProteinConditionalSearch(input)
}

const proteinsFromComplexes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/complexes/proteins', description: descriptions.complexes_proteins } })
  .input(complexQueryFormat.merge(z.object({ verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(proteinComplexFormat))
  .query(async ({ input }) => await conditionalSearch(input))

const complexesFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/complexes', description: descriptions.proteins_complexes } })
  .input(proteinsQueryFormat.merge(z.object({ verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(proteinComplexFormat))
  .query(async ({ input }) => await conditionalProteinSearch(input))

export const complexesProteinsRouters = {
  proteinsFromComplexes,
  complexesFromProteins
}
