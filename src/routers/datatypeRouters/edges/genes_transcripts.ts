import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { transcriptFormat, transcriptsQueryFormat } from '../nodes/transcripts'
import { geneFormat, genesQueryFormat } from '../nodes/genes'
import { proteinFormat, proteinsQueryFormat } from '../nodes/proteins'

const schema = loadSchemaConfig()

// primary: genes_transcripts
const schemaObj = schema['transcribed to']

// secondary: transcripts_proteins
const secondarySchemaObj = schema['translates to']

const routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))

const transcriptsFromGeneID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/{gene_id}/transcripts' } })
  .input(z.object({ gene_id: z.string(), page: z.number().default(0) }))
  .output(z.array(transcriptFormat))
  .query(async ({ input }) => await routerEdge.getTargetsByID(input.gene_id, input.page, 'chr'))

const transcriptsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/transcripts' } })
  .input(genesQueryFormat)
  .output(z.array(transcriptFormat))
  .query(async ({ input }) => await routerEdge.getTargets(input, 'chr'))

const genesFromTranscriptsByID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/transcripts/{transcript_id}/genes' } })
  .input(z.object({ transcript_id: z.string(), page: z.number().default(0) }))
  .output(z.array(geneFormat))
  .query(async ({ input }) => await routerEdge.getSourcesByID(input.transcript_id, input.page, 'chr'))

const genesFromTranscripts = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/transcripts/genes' } })
  .input(transcriptsQueryFormat)
  .output(z.array(geneFormat))
  .query(async ({ input }) => await routerEdge.getSources(input, 'chr'))

const proteinsFromGeneID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/{gene_id}/proteins' } })
  .input(z.object({ gene_id: z.string(), page: z.number().default(0) }))
  .output(z.array(proteinFormat))
  .query(async ({ input }) => await routerEdge.getSecondaryTargetsByID(input.gene_id, input.page, 'chr'))

const proteinsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/proteins' } })
  .input(genesQueryFormat)
  .output(z.array(proteinFormat))
  .query(async ({ input }) => await routerEdge.getSecondaryTargets(input, 'chr'))

const genesFromProteinID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/{protein_id}/genes' } })
  .input(z.object({ protein_id: z.string(), page: z.number().default(0) }))
  .output(z.array(geneFormat))
  .query(async ({ input }) => await routerEdge.getSecondarySourcesByID(input.protein_id, input.page, 'chr'))

const genesFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/genes' } })
  .input(proteinsQueryFormat)
  .output(z.array(geneFormat))
  .query(async ({ input }) => await routerEdge.getSecondarySources(input, 'chr'))

export const genesTranscriptsRouters = {
  transcriptsFromGenes,
  transcriptsFromGeneID,
  genesFromTranscripts,
  genesFromTranscriptsByID,
  proteinsFromGenes,
  proteinsFromGeneID,
  genesFromProteins,
  genesFromProteinID
}
