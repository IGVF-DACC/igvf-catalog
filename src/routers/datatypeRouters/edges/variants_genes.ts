import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

const variantsEqtlQueryFormat = z.object({
  // beta: z.string().optional(), NOTE: temporarily removing to optimize queries
  p_value: z.string().optional(),
  // slope: z.string().optional(), NOTE: temporarily removing to optimize queries
  verbose: z.enum(['true', 'false']).default('false'),
  // source: z.string().optional(), NOTE: all entries have GTEx value
  page: z.number().default(0)
})

const variantsSqtlQueryFormat = z.object({
  // beta: z.string().optional(), NOTE: temporarily removing to optimize queries
  p_value: z.string().optional(),
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

const eqtls = schema['gtex variant to gene expression association']
const sqtls = schema['gtex splice variant to gene association']
const qtls = schema['variant to gene association']
const geneTranscripts = schema['transcribed to']

const routerGenesTranscripts = new RouterEdges(geneTranscripts)

const routerEqtls = new RouterEdges(eqtls)
const routerSqtls = new RouterEdges(sqtls)
const routerQtls = new RouterEdges(qtls, routerGenesTranscripts)

async function conditionalSearch (input: paramsFormatType, type: string): Promise<any[]> {
  const verbose = input.verbose === 'true'
  delete input.verbose

  if ('variant_id' in input) {
    input._from = `variants/${input.variant_id as string}`
    delete input.variant_id
  }

  if ('gene_id' in input) {
    input._to = `genes/${input.gene_id as string}`
    delete input.gene_id
  }

  if (type === 'eqtl') {
    input.label = 'eQTL'
    input.sort = '_key'
    return await routerEqtls.getEdgeObjects(input, '', verbose)
  }

  const preProcessed = preProcessRegionParam({ ...input, ...{ sort: '_key' } }, null, 'intron')

  if (type === 'sqtl') {
    input.label = 'splice_QTL'
    return await routerSqtls.getEdgeObjects(preProcessed, '', verbose)
  }

  return await routerQtls.getEdgeObjects(preProcessed, '', verbose)
}

const sqtlFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/s-qtls', description: descriptions.variants_genes_sqtl } })
  .input(variantsSqtlQueryFormat)
  .output(z.array(sqtlFormat))
  .query(async ({ input }) => await conditionalSearch(input, 'sqtl'))

const eqtlFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/e-qtls', description: descriptions.variants_genes_eqtl } })
  .input(variantsEqtlQueryFormat)
  .output(z.array(eqtlFormat))
  .query(async ({ input }) => await conditionalSearch(input, 'eqtl'))

const genesFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/genes', description: descriptions.variants_id_genes } })
  .input(z.object({ variant_id: z.string() }).merge(variantsEqtlQueryFormat))
  .output(z.array(eqtlFormat.merge(sqtlFormat)))
  .query(async ({ input }) => await conditionalSearch(input, 'all'))

const variantsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/{gene_id}/variants', description: descriptions.genes_variants } })
  .input(z.object({ gene_id: z.string() }).merge(variantsEqtlQueryFormat))
  .output(z.array(eqtlFormat))
  .query(async ({ input }) => await conditionalSearch(input, 'all'))

export const variantsGenesRouters = {
  eqtlFromVariants,
  sqtlFromVariants,
  variantsFromGenes,
  genesFromVariants
}
