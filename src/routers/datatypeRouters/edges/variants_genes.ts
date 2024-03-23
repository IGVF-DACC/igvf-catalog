import { z } from 'zod'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam, validRegion } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { geneFormat } from '../nodes/genes'

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

async function nearestGeneSearch (input: paramsFormatType): Promise<any[]> {
  const regionParams = validRegion(input.region as string)

  if (regionParams === null) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Region format invalid. Please use the format as the example: "chr1:12345-54321"'
    })
  }

  const inRegionQuery = `
    FOR record in genes
    FILTER ${getFilterStatements(schema['sequence variant'], preProcessRegionParam(input))}
    RETURN {${getDBReturnStatements(schema['gene'])}}
  `

  const codingRegionGenes = await (await db.query(inRegionQuery)).all()

  if (codingRegionGenes.length !== 0) {
    return codingRegionGenes
  }

  const nearestQuery = `
    LET LEFT = (
      FOR record in genes
      FILTER record.chr == '${regionParams[1]}' and record['end:long'] < ${regionParams[2]}
      SORT record['end:long'] DESC
      LIMIT 1
      RETURN {${getDBReturnStatements(schema['gene'])}}
    )

    LET RIGHT = (
      FOR record in genes
      FILTER record.chr == '${regionParams[1]}' and record['start:long'] > ${regionParams[3]}
      SORT record['start:long']
      LIMIT 1
      RETURN {${getDBReturnStatements(schema['gene'])}}
    )

    RETURN UNION(LEFT, RIGHT)[0]
  `

  return await (await db.query(nearestQuery)).all()
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

// temporary format rearrangement until genes.ts is refactored
const geneOutputFormat = geneFormat.omit({_id: true}).merge(z.object({id: z.string()}))
const nearest_genes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/nearest-genes', description: descriptions.nearest_genes } })
  .input(z.object({ region: z.string().trim() }))
  .output(z.array(geneOutputFormat))
  .query(async ({ input }) => await nearestGeneSearch(input))

export const variantsGenesRouters = {
  genesFromVariants,
  variantsFromGenes,
  nearest_genes
}
