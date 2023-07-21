import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'
import { preProcessRegionParam } from '../_helpers'

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

const transcriptsQueryFormat = z.object({
  region: z.string().optional(),
  transcript_type: transcriptTypes.optional(),
  page: z.number().default(0)
})

const transcriptFormat = z.object({
  _id: z.string(),
  transcript_type: z.string(),
  chr: z.string(),
  start: z.number(),
  end: z.number(),
  transcript_name: z.string(),
  gene_name: z.string(),
  source: z.string(),
  version: z.string(),
  source_url: z.any()
})

const schemaObj = schema.transcript
const router = new RouterFilterBy(schemaObj)
const routerID = new RouterFilterByID(schemaObj)

const transcripts = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: router.apiSpecs.description } })
  .input(transcriptsQueryFormat)
  .output(z.array(transcriptFormat))
  .query(async ({ input }) => await router.getObjects(preProcessRegionParam(input)))

export const transcriptID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${routerID.path}` } })
  .input(z.object({ id: z.string() }))
  .output(transcriptFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))

export const transcriptsRouters = {
  transcripts,
  transcriptID
}