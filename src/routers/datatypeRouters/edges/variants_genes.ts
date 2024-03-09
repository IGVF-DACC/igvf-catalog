import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'

// Values calculated from database to optimize range queries
// MAX pvalue = 0.00175877, MAX -log10 pvalue = 306.99234812274665 (from datasets)
const MAX_LOG10_PVALUE = 400
const MAX_BETA = 0.158076
const MAX_SLOPE = 8.66426

const schema = loadSchemaConfig()

const variantsQtlsQueryFormat = z.object({
  beta: z.string().optional(),
  log10pvalue: z.string().trim().optional(),
  label: z.enum(['eQTL', 'splice_QTL']).optional(),
  slope: z.string().optional(),
  // intron_region: z.string().optional(), // NOTE: temporarily removing to optimize queries, zkd doesn't support null values
  verbose: z.enum(['true', 'false']).default('false'),
  // source: z.string().optional(), NOTE: all entries have GTEx value
  page: z.number().default(0)
})

const sqtlFormat = z.object({
  'sequence variant': z.any().nullable(),
  gene: z.any().nullable(),
  log10pvalue: z.number().or(z.string()).nullable(),
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
  log10pvalue: z.number().or(z.string()).nullable(),
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

function raiseInvalidParameters (param: string): void {
  throw new TRPCError({
    code: 'BAD_REQUEST',
    message: `${param} must be a query range using: gte, lte, gt, or lt. For example: lte:0.001`
  })
}

async function qtlSearch (input: paramsFormatType): Promise<any[]> {
  const verbose = input.verbose === 'true'
  delete input.verbose

  const customFilters = []

  input.sort = '_key'

  if ('intron_region' in input) {
    input = preProcessRegionParam({ ...input }, null, 'intron')
  }

  if ('beta' in input) {
    customFilters.push(`record['beta:long'] <= ${MAX_BETA}`)
    if (!(input.beta as string).includes(':')) {
      raiseInvalidParameters('beta')
    }
  }

  if ('log10pvalue' in input) {
    customFilters.push(`record['log10pvalue:long'] <= ${MAX_LOG10_PVALUE}`)
    if (!(input.log10pvalue as string).includes(':')) {
      raiseInvalidParameters('log10pvalue')
    }
  }

  if ('slope' in input) {
    customFilters.push(`record['slope:long'] <= ${MAX_SLOPE}`)
    if (!(input.slope as string).includes(':')) {
      raiseInvalidParameters('slope')
    }
  }

  if ('variant_id' in input) {
    input._from = `variants/${input.variant_id as string}`
    delete input.variant_id
  }

  if ('gene_id' in input) {
    input._to = `genes/${input.gene_id as string}`
    delete input.gene_id
  }

  const objects = await routerQtls.getEdgeObjects(input, '', verbose, `${customFilters.join(' AND ')}`)

  for (let index = 0; index < objects.length; index++) {
    const element = objects[index]
    if (element['log10pvalue'] == MAX_LOG10_PVALUE) {
      objects[index]['log10pvalue'] = 'inf'
    }
  }

  return objects
}
const genesFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/genes', description: descriptions.variants_genes } })
  .input(z.object({ variant_id: z.string().trim().optional() }).merge(variantsQtlsQueryFormat))
  .output(z.array(eqtlFormat.merge(sqtlFormat)))
  .query(async ({ input }) => await qtlSearch(input))

const variantsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/variants', description: descriptions.genes_variants } })
  .input(z.object({ gene_id: z.string().trim().optional() }).merge(variantsQtlsQueryFormat))
  .output(z.array(eqtlFormat))
  .query(async ({ input }) => await qtlSearch(input))

export const variantsGenesRouters = {
  genesFromVariants,
  variantsFromGenes
}
