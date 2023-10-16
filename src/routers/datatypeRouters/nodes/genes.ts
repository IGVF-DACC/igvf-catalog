import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'
import { paramsFormatType, preProcessRegionParam } from '../_helpers'
import { RouterFuzzy } from '../../genericRouters/routerFuzzy'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

const geneTypes = z.enum([
  'IG_V_pseudogene',
  'lncRNA',
  'miRNA',
  'misc_RNA',
  'processed_pseudogene',
  'protein_coding',
  'pseudogene',
  'rRNA',
  'rRNA_pseudogene',
  'scaRNA',
  'snoRNA',
  'snRNA',
  'TEC',
  'transcribed_processed_pseudogene',
  'transcribed_unitary_pseudogene',
  'transcribed_unprocessed_pseudogene',
  'unitary_pseudogene',
  'unprocessed_pseudogene',
  'ribozyme',
  'translated_unprocessed_pseudogene',
  'sRNA',
  'IG_C_gene',
  'IG_C_pseudogene',
  'IG_D_gene',
  'IG_J_gene',
  'IG_J_pseudogene',
  'IG_pseudogene',
  'IG_V_gene',
  'TR_C_gene',
  'TR_D_gene',
  'TR_J_gene',
  'TR_J_pseudogene',
  'TR_V_gene',
  'TR_V_pseudogene',
  'translated_processed_pseudogene',
  'scRNA',
  'artifact',
  'vault_RNA',
  'Mt_rRNA',
  'Mt_tRNA'
])

export const genesQueryFormat = z.object({
  gene_name: z.string().optional(), // fuzzy search
  region: z.string().optional(),
  gene_type: geneTypes.optional(),
  alias: z.string().optional(),
  page: z.number().default(0)
})

export const geneFormat = z.object({
  _id: z.string(),
  chr: z.string(),
  start: z.number().nullable(),
  end: z.number().nullable(),
  gene_type: z.string().nullable(),
  gene_name: z.string(),
  source: z.string(),
  version: z.any(),
  source_url: z.any(),
  alias: z.array(z.string()).optional().nullable()
})

const schemaObj = schema.gene
const router = new RouterFilterBy(schemaObj)
const routerID = new RouterFilterByID(schemaObj)
const routerFuzzy = new RouterFuzzy(schemaObj)

async function conditionalSearch (input: paramsFormatType): Promise<any[]> {
  const preProcessed = preProcessRegionParam({ ...input, ...{ sort: 'chr' } })

  const exactMatch = await router.getObjects(preProcessed)

  if (preProcessed.gene_name !== undefined && exactMatch.length === 0) {
    const term = preProcessed.gene_name as string
    delete preProcessed.gene_name
    return await routerFuzzy.getObjectsByFuzzyTextSearch(term, input.page as number, router.getFilterStatements(preProcessed))
  }

  return exactMatch
}

const genes = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: descriptions.genes } })
  .input(genesQueryFormat)
  .output(z.array(geneFormat))
  .query(async ({ input }) => await conditionalSearch(input))

export const geneID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${routerID.path}`, description: descriptions.genes_id } })
  .input(z.object({ id: z.string() }))
  .output(geneFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))

export const genesRouters = {
  geneID,
  genes
}
