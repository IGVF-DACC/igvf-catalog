import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { transcriptFormat, transcriptsQueryFormat } from '../nodes/transcripts'
import { proteinFormat, proteinsQueryFormat } from '../nodes/proteins'

const schema = loadSchemaConfig()

// primary: transcripts_proteins
const schemaObj = schema['translates to']

const routerEdge = new RouterEdges(schemaObj)

const proteinsFromTranscriptID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/transcripts/{transcript_id}/proteins' } })
  .input(z.object({ transcript_id: z.string(), page: z.number().default(0) }))
  .output(z.array(proteinFormat))
  .query(async ({ input }) => await routerEdge.getTargetsByID(input.transcript_id, input.page, 'chr'))

const proteinsFromTranscripts = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/transcripts/proteins' } })
  .input(transcriptsQueryFormat)
  .output(z.array(proteinFormat))
  .query(async ({ input }) => await routerEdge.getTargets(input, 'chr'))

const transcriptsFromProteinID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/{protein_id}/transcripts' } })
  .input(z.object({ protein_id: z.string(), page: z.number().default(0) }))
  .output(z.array(transcriptFormat))
  .query(async ({ input }) => await routerEdge.getSourcesByID(input.protein_id, input.page, 'chr'))

const transcriptsFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/transcripts' } })
  .input(proteinsQueryFormat)
  .output(z.array(transcriptFormat))
  .query(async ({ input }) => await routerEdge.getSources(input, 'chr'))

export const transcriptsProteinsRouters = {
  proteinsFromTranscripts,
  proteinsFromTranscriptID,
  transcriptsFromProteins,
  transcriptsFromProteinID
}
