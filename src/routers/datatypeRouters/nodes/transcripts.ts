import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'
import { paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

const transcriptTypes = z.enum([
  'rRNA_pseudogene',
  'misc_RNA',
  'protein_coding',
  'protein_coding_CDS_not_defined',
  'unprocessed_pseudogene',
  'retained_intron',
  'nonsense_mediated_decay',
  'lncRNA',
  'processed_pseudogene',
  'transcribed_processed_pseudogene',
  'processed_transcript',
  'protein_coding_LoF',
  'transcribed_unprocessed_pseudogene',
  'transcribed_unitary_pseudogene',
  'non_stop_decay',
  'snoRNA',
  'TEC',
  'scaRNA',
  'miRNA',
  'snRNA',
  'pseudogene',
  'unitary_pseudogene',
  'IG_V_pseudogene',
  'rRNA',
  'ribozyme',
  'translated_unprocessed_pseudogene',
  'sRNA',
  'IG_pseudogene',
  'TR_V_gene',
  'IG_C_gene',
  'IG_D_gene',
  'IG_C_pseudogene',
  'IG_J_gene',
  'IG_J_pseudogene',
  'IG_V_gene',
  'TR_C_gene',
  'TR_J_gene',
  'TR_J_pseudogene',
  'TR_V_pseudogene',
  'TR_D_gene',
  'translated_processed_pseudogene',
  'scRNA',
  'artifact',
  'vault_RNA',
  'Mt_rRNA',
  'Mt_tRNA'
])

export const transcriptsQueryFormat = z.object({
  organism: z.enum(['human', 'mouse']).default('human'),
  transcript_id: z.string().trim().optional(),
  region: z.string().trim().optional(),
  transcript_type: transcriptTypes.optional(),
  page: z.number().default(0)
})

export const transcriptFormat = z.object({
  _id: z.string(),
  transcript_type: z.string(),
  chr: z.string(),
  start: z.number(),
  end: z.number(),
  name: z.string(),
  gene_name: z.string(),
  source: z.string(),
  version: z.string(),
  source_url: z.any()
})

const humanSchemaObj = schema.transcript
const humanRouter = new RouterFilterBy(humanSchemaObj)
const humanRouterID = new RouterFilterByID(humanSchemaObj)

const mouseSchemaObj = schema['transcript mouse']
const mouseRouter = new RouterFilterBy(mouseSchemaObj)
const mouseRouterID = new RouterFilterByID(mouseSchemaObj)

async function conditionalTranscriptSearch (input: paramsFormatType): Promise<any[]> {
  let router = humanRouter
  let routerID = humanRouterID

  if (input.organism === 'mouse') {
    router = mouseRouter
    routerID = mouseRouterID
  }

  delete input.organism

  if (input.transcript_id !== undefined) {
    return await routerID.getObjectById(input.transcript_id as string)
  }

  return await router.getObjects(preProcessRegionParam({ ...input, ...{ sort: 'chr' } }))
}

const transcripts = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/transcripts', description: descriptions.transcripts } })
  .input(transcriptsQueryFormat)
  .output(z.array(transcriptFormat).or(transcriptFormat))
  .query(async ({ input }) => await conditionalTranscriptSearch(input))

export const transcriptsRouters = {
  transcripts
}
