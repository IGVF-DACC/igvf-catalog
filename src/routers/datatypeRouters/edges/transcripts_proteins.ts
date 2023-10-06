import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { transcriptFormat, transcriptsQueryFormat } from '../nodes/transcripts'
import { proteinFormat, proteinsQueryFormat } from '../nodes/proteins'

const proteinTranscriptFormat = z.object({
  source: z.string().optional(),
  source_url: z.string().optional(),
  protein: z.string().or(z.array(proteinFormat)).optional(),
  transcript: z.string().or(z.array(transcriptFormat)).optional()
})

const schema = loadSchemaConfig()

// primary: transcripts_proteins
const schemaObj = schema['translates to']

const routerEdge = new RouterEdges(schemaObj)

const proteinsFromTranscriptID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/transcripts/{transcript_id}/proteins' } })
  .input(z.object({ transcript_id: z.string(), page: z.number().default(0), verbose: z.enum(['true', 'false']).default('false') }))
  .output(z.array(proteinTranscriptFormat))
  .query(async ({ input }) => await routerEdge.getTargetsByID(input.transcript_id, input.page, 'chr', input.verbose === 'true'))

const proteinsFromTranscripts = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/transcripts/proteins' } })
  .input(transcriptsQueryFormat.merge(z.object({ verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(proteinTranscriptFormat))
  .query(async ({ input }) => await routerEdge.getTargets(input, 'chr', input.verbose === 'true'))

const transcriptsFromProteinID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/{protein_id}/transcripts' } })
  .input(z.object({ protein_id: z.string(), page: z.number().default(0), verbose: z.enum(['true', 'false']).default('false') }))
  .output(z.array(proteinTranscriptFormat))
  .query(async ({ input }) => await routerEdge.getSourcesByID(input.protein_id, input.page, 'chr', input.verbose === 'true'))

const transcriptsFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/transcripts' } })
  .input(proteinsQueryFormat.merge(z.object({ verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(proteinTranscriptFormat))
  .query(async ({ input }) => await routerEdge.getSources(input, 'chr', input.verbose === 'true'))

export const transcriptsProteinsRouters = {
  proteinsFromTranscripts,
  proteinsFromTranscriptID,
  transcriptsFromProteins,
  transcriptsFromProteinID
}
