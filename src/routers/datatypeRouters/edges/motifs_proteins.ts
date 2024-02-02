import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { proteinFormat, proteinsQueryFormat } from '../nodes/proteins'
import { motifFormat, motifsQueryFormat } from '../nodes/motifs'
import { paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

const motifsToProteinsFormat = z.object({
  source: z.string().optional(),
  protein: z.string().or(z.array(proteinFormat)).optional(),
  motif: z.string().or(z.array(motifFormat)).optional()
})

const schemaObj = schema['motif to protein']

const router = new RouterEdges(schemaObj)

// could reload motifs to change that property name instead
function preProcessInput (input: paramsFormatType): paramsFormatType {
  if (input.name !== undefined) {
    input.tf_name = (input.name as string).toUpperCase()
  }
  delete input.name
  return input
}

async function conditionalProteinSearch (input: paramsFormatType): Promise<any[]> {
  if (input.protein_id !== undefined) {
    return await router.getSourcesByID(input.protein_id as string, input.page as number, '_key', input.verbose === 'true')
  }

  return await router.getSources(input, '_key', input.verbose === 'true')
}

const motifsFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/motifs', description: descriptions.proteins_motifs } })
  .input(proteinsQueryFormat.omit({ organism: true }).merge(z.object({ verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(motifsToProteinsFormat))
  .query(async ({ input }) => await conditionalProteinSearch(input))

// motifs shouldn't need query by ID endpoints
const proteinsFromMotifs = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/motifs/proteins', description: descriptions.motifs_proteins } })
  .input(motifsQueryFormat.merge(z.object({ verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(motifsToProteinsFormat))
  .query(async ({ input }) => await router.getTargets(preProcessInput(input), '_key', input.verbose === 'true'))

export const motifsProteinsRouters = {
  proteinsFromMotifs,
  motifsFromProteins
}
