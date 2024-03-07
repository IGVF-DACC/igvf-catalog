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
  organism: z.enum(['human', 'mouse']).default('human'),
  gene_id: z.string().trim().optional(),
  name: z.string().trim().optional(), // fuzzy search
  region: z.string().trim().optional(),
  gene_type: geneTypes.optional(),
  hgnc: z.string().trim().optional(),
  alias: z.string().trim().optional(), // fuzzy search
  page: z.number().default(0)
})

export const geneFormat = z.object({
  _id: z.string(),
  chr: z.string(),
  start: z.number().nullable(),
  end: z.number().nullable(),
  gene_type: z.string().nullable(),
  name: z.string(),
  hgnc: z.string().optional().nullable(),
  source: z.string(),
  version: z.any(),
  source_url: z.any(),
  alias: z.array(z.string()).optional().nullable()
})

const humanSchemaObj = schema.gene
const mouseSchemaObj = schema['gene mouse']

const humanRouter = new RouterFilterBy(humanSchemaObj)
const humanRouterID = new RouterFilterByID(humanSchemaObj)
const humanRouterSearch = new RouterFuzzy(humanSchemaObj)

const mouseRouter = new RouterFilterBy(mouseSchemaObj)
const mouseRouterID = new RouterFilterByID(mouseSchemaObj)
const mouseRouterSearch = new RouterFuzzy(mouseSchemaObj)

async function conditionalSearch (input: paramsFormatType): Promise<any[]> {
  let router = humanRouter
  let routerID = humanRouterID
  let routerSearch = humanRouterSearch

  if (input.organism === 'mouse') {
    router = mouseRouter
    routerID = mouseRouterID
    routerSearch = mouseRouterSearch
  }

  delete input.organism

  if (input.gene_id !== undefined) {
    return await routerID.getObjectById(input.gene_id as string)
  }
  const preProcessed = preProcessRegionParam({ ...input, ...{ sort: 'chr' } })
  if ('gene_name' in input || 'alias' in input) {
    const geneName = preProcessed.name as string
    delete preProcessed.name

    const alias = preProcessed.alias as string
    delete preProcessed.alias

    const remainingFilters = router.getFilterStatements(preProcessed)

    const searchTerms = { name: geneName, alias }
    const textObjects = await routerSearch.textSearch(searchTerms, 'token', input.page as number, remainingFilters)
    if (textObjects.length === 0) {
      return await routerSearch.textSearch(searchTerms, 'fuzzy', input.page as number, remainingFilters)
    }
    return textObjects
  }
  const exactMatch = await router.getObjects(preProcessed)
  return exactMatch
}

const genes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes', description: descriptions.genes } })
  .input(genesQueryFormat)
  .output(z.array(geneFormat).or(geneFormat))
  .query(async ({ input }) => await conditionalSearch(input))

export const genesRouters = {
  genes
}
