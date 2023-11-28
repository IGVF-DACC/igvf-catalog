import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { paramsFormatType, preProcessRegionParam } from '../_helpers'

const schema = loadSchemaConfig()

const variantsQtlsQueryFormat = z.object({
  // beta: z.string().optional(), NOTE: temporarily removing to optimize queries
  p_value: z.string().optional(),
  label: z.enum(['eQTL', 'splice_QTL']).optional(),
  // slope: z.string().optional(), NOTE: temporarily removing to optimize queries
  // intron_region: z.string().optional(), NOTE: temporarily removing to optimize queries
  verbose: z.enum(['true', 'false']).default('false'),
  // source: z.string().optional(), NOTE: all entries have GTEx value
  page: z.number().default(0)
})

const sqtlFormat = z.object({
  'sequence variant': z.any().nullable(),
  gene: z.any().nullable(),
  p_value: z.number().nullable(),
  slope: z.number(),
  beta: z.number(),
  label: z.string(),
  source: z.string(),
  biological_context: z.string(),
  intron_chr: z.string().nullable(),
  intron_start: z.number().nullable(),
  intron_end: z.number().nullable()
})

const eqtlFormat = z.object({
  'sequence variant': z.any().nullable(),
  gene: z.any().nullable(),
  beta: z.number(),
  label: z.string(),
  p_value: z.number().nullable(),
  slope: z.number(),
  source: z.string(),
  source_url: z.string().optional(),
  biological_context: z.string(),
  chr: z.string().optional()
})

const qtls = schema['variant to gene association']
const geneTranscripts = schema['transcribed to']

const routerGenesTranscripts = new RouterEdges(geneTranscripts)

const routerQtls = new RouterEdges(qtls, routerGenesTranscripts)

async function qtlSearch (input: paramsFormatType): Promise<any[]> {
  const verbose = input.verbose === 'true'
  delete input.verbose

  input.sort = '_key'

  if ('intron_region' in input) {
    input = preProcessRegionParam({ ...input }, null, 'intron')
  }

  if ('variant_id' in input) {
    input._from = `variants/${input.variant_id as string}`
    delete input.variant_id
  }

  if ('gene_id' in input) {
    input._to = `genes/${input.gene_id as string}`
    delete input.gene_id
  }

  return await routerQtls.getEdgeObjects(input, '', verbose)
}
const genesFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/genes' } })
  .input(z.object({ variant_id: z.string().optional() }).merge(variantsQtlsQueryFormat))
  .output(z.array(eqtlFormat.merge(sqtlFormat)))
  .query(async ({ input }) => await qtlSearch(input))

const variantsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/variants' } })
  .input(z.object({ gene_id: z.string().trim().optional() }).merge(variantsQtlsQueryFormat))
  .output(z.array(eqtlFormat))
  .query(async ({ input }) => await qtlSearch(input))

export const variantsGenesRouters = {
  genesFromVariants,
  variantsFromGenes
}
