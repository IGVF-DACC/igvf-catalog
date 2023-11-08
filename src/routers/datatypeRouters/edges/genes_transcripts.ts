import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { transcriptFormat, transcriptsQueryFormat } from '../nodes/transcripts'
import { geneFormat, genesQueryFormat } from '../nodes/genes'
import { proteinFormat, proteinsQueryFormat } from '../nodes/proteins'
import { paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'

const genesTranscriptsFormat = z.object({
  source: z.string().optional(),
  source_url: z.string().optional(),
  version: z.string().optional(),
  gene: z.string().or(z.array(geneFormat)).optional(),
  transcript: z.string().or(z.array(transcriptFormat)).optional()
})

const schema = loadSchemaConfig()

// primary: genes_transcripts
const schemaObj = schema['transcribed to']

// secondary: transcripts_proteins
const secondarySchemaObj = schema['translates to']

const routerEdge = new RouterEdges(schemaObj, new RouterEdges(secondarySchemaObj))

async function conditionalTranscriptSearch (input: paramsFormatType): Promise<any[]> {
  if (input.transcript_id !== undefined) {
    return await routerEdge.getSourcesByID(input.transcript_id as string, input.page as number, 'chr', input.verbose === 'true')
  }

  return await routerEdge.getSources(input, 'chr', input.verbose === 'true')
}

const transcriptsFromGeneID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/{gene_id}/transcripts', description: descriptions.genes_id_transcripts } })
  .input(z.object({ gene_id: z.string(), page: z.number().default(0), verbose: z.enum(['true', 'false']).default('false') }))
  .output(z.array(genesTranscriptsFormat))
  .query(async ({ input }) => await routerEdge.getTargetsByID(input.gene_id, input.page, 'chr', input.verbose === 'true'))

const transcriptsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/transcripts', description: descriptions.genes_transcripts } })
  .input(genesQueryFormat.merge(z.object({ verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(genesTranscriptsFormat))
  .query(async ({ input }) => await routerEdge.getTargets(input, 'chr', input.verbose === 'true'))

const genesFromTranscripts = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/transcripts/genes', description: descriptions.transcripts_genes } })
  .input(transcriptsQueryFormat.merge(z.object({ verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(genesTranscriptsFormat))
  .query(async ({ input }) => await conditionalTranscriptSearch(input))

const proteinsFromGeneID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/{gene_id}/proteins', description: descriptions.genes_id_proteins } })
  .input(z.object({ gene_id: z.string(), page: z.number().default(0) }))
  .output(z.array(proteinFormat))
  .query(async ({ input }) => await routerEdge.getSecondaryTargetsByID(input.gene_id, input.page, 'chr'))

const proteinsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/proteins', description: descriptions.genes_proteins } })
  .input(genesQueryFormat)
  .output(z.array(proteinFormat))
  .query(async ({ input }) => await routerEdge.getSecondaryTargets(input, 'chr'))

const genesFromProteinID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/{protein_id}/genes', description: descriptions.proteins_id_genes } })
  .input(z.object({ protein_id: z.string(), page: z.number().default(0) }))
  .output(z.array(geneFormat))
  .query(async ({ input }) => await routerEdge.getSecondarySourcesByID(input.protein_id, input.page, 'chr'))

const genesFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/genes', description: descriptions.proteins_genes } })
  .input(proteinsQueryFormat)
  .output(z.array(geneFormat))
  .query(async ({ input }) => await routerEdge.getSecondarySources(input, 'chr'))

export const genesTranscriptsRouters = {
  transcriptsFromGeneID,
  transcriptsFromGenes,
  genesFromTranscripts,
  proteinsFromGeneID,
  proteinsFromGenes,
  genesFromProteinID,
  genesFromProteins
}
