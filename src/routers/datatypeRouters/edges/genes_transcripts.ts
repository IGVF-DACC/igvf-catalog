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

async function conditionalProteinSearch (input: paramsFormatType): Promise<any[]> {
  if (input.protein_id !== undefined) {
    return await routerEdge.getSecondarySourcesByID(input.protein_id as string, input.page as number, 'chr')
  }

  return await routerEdge.getSecondarySources(input, 'chr')
}

async function conditionalGeneProteinSearch (input: paramsFormatType): Promise<any[]> {
  if (input.gene_id !== undefined) {
    return await routerEdge.getSecondaryTargetsByID(input.gene_id as string, input.page as number, 'chr')
  }

  return await routerEdge.getSecondaryTargets(input, 'chr')
}

async function conditionalGeneTranscriptSearch (input: paramsFormatType): Promise<any[]> {
  if (input.gene_id !== undefined) {
    return await routerEdge.getTargetsByID(input.gene_id as string, input.page as number, 'chr', input.verbose === 'true')
  }

  return await routerEdge.getTargets(input, 'chr', input.verbose === 'true')
}

async function conditionalTranscriptSearch (input: paramsFormatType): Promise<any[]> {
  if (input.transcript_id !== undefined) {
    return await routerEdge.getSourcesByID(input.transcript_id as string, input.page as number, 'chr', input.verbose === 'true')
  }

  return await routerEdge.getSources(input, 'chr', input.verbose === 'true')
}

const transcriptsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/transcripts', description: descriptions.genes_transcripts } })
  .input(genesQueryFormat.omit({ organism: true }).merge(z.object({ verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(genesTranscriptsFormat))
  .query(async ({ input }) => await conditionalGeneTranscriptSearch(input))

const genesFromTranscripts = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/transcripts/genes', description: descriptions.transcripts_genes } })
  .input(transcriptsQueryFormat.omit({ organism: true }).merge(z.object({ verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(genesTranscriptsFormat))
  .query(async ({ input }) => await conditionalTranscriptSearch(input))

const proteinsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/proteins', description: descriptions.genes_proteins } })
  .input(genesQueryFormat.omit({ organism: true }))
  .output(z.array(proteinFormat))
  .query(async ({ input }) => await conditionalGeneProteinSearch(input))

const genesFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/genes', description: descriptions.proteins_genes } })
  .input(proteinsQueryFormat.omit({ organism: true }))
  .output(z.array(geneFormat))
  .query(async ({ input }) => await conditionalProteinSearch(input))

export const genesTranscriptsRouters = {
  transcriptsFromGenes,
  genesFromTranscripts,
  proteinsFromGenes,
  genesFromProteins
}
