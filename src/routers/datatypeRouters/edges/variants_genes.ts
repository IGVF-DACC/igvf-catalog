import { z } from 'zod'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam, validRegion } from '../_helpers'
import { QUERY_LIMIT } from '../../../constants'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { geneFormat, geneSearch } from '../nodes/genes'
import { commonHumanEdgeParamsFormat, genesCommonQueryFormat, variantsCommonQueryFormat } from '../params'
import { variantSearch, singleVariantQueryFormat, variantFormat, variantIDSearch } from '../nodes/variants'

const MAX_PAGE_SIZE = 500

// Values calculated from database to optimize range queries
// MAX pvalue = 0.00175877, MAX -log10 pvalue = 306.99234812274665 (from datasets)
const MAX_LOG10_PVALUE = 400
const MAX_SLOPE = 8.66426 // i.e. effect_size

const schema = loadSchemaConfig()

const QtlSources = z.enum(['GTEx', 'AFGR'])

const qtlsSummaryFormat = z.object({
  qtl_type: z.string(),
  log10pvalue: z.number(),
  chr: z.string(),
  biological_context: z.string().nullish(),
  effect_size: z.number().nullish(),
  pval_beta: z.number().nullish(),
  gene: z.object({
    gene_name: z.string(),
    gene_id: z.string(),
    gene_start: z.number(),
    gene_end: z.number()
  })
})

const variantsGenesQueryFormat = z.object({
  log10pvalue: z.string().trim().optional(),
  effect_size: z.string().optional(),
  label: z.enum(['eQTL', 'splice_QTL']).optional(),
  source: QtlSources.optional()
})

const geneQueryFormat = genesCommonQueryFormat.merge(variantsGenesQueryFormat).merge(commonHumanEdgeParamsFormat)

const sqtlFormat = z.object({
  'sequence variant': z.string().or(variantFormat).nullable(),
  gene: z.string().or(geneFormat).nullable(),
  log10pvalue: z.number().or(z.string()).nullable(),
  effect_size: z.number(),
  label: z.string(),
  source: z.string(),
  biological_context: z.string(),
  intron_chr: z.string().nullable(),
  intron_start: z.number().nullable(),
  intron_end: z.number().nullable()
})

const eqtlFormat = z.object({
  'sequence variant': z.string().or(variantFormat).nullable(),
  gene: z.string().or(geneFormat).nullable(),
  label: z.string(),
  log10pvalue: z.number().or(z.string()).nullable(),
  effect_size: z.number(),
  source: z.string(),
  source_url: z.string().optional(),
  biological_context: z.string(),
  chr: z.string().optional()
})

const qtls = schema['variant to gene association']
const variantSchema = schema['sequence variant']
const geneSchema = schema.gene

function raiseInvalidParameters (param: string): void {
  throw new TRPCError({
    code: 'BAD_REQUEST',
    message: `${param} must be a query range using: gte, lte, gt, or lt. For example: lte:0.001`
  })
}

export async function qtlSummary (input: paramsFormatType): Promise<any> {
  input.page = 0
  const variant = (await variantSearch(input))

  if (variant.length === 0) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Variant not found.'
    })
  }

  const targetQuery = `FOR otherRecord IN genes
  FILTER otherRecord._id == record._to
  RETURN {
    gene_name: otherRecord.name,
    gene_id: otherRecord._key,
    gene_start: otherRecord['start:long'],
    gene_end: otherRecord['end:long'],
  }
  `

  const query = `
    FOR record IN variants_genes
    FILTER record._from == 'variants/${variant[0]._id as string}'
    RETURN {
      qtl_type: record.label,
      log10pvalue: record['log10pvalue:long'],
      chr: record.chr,
      biological_context: record.biological_context,
      effect_size: record['effect_size:long'],
      pval_beta: record['pval_beta:long'],
      'gene': (${targetQuery})[0]
    }
  `

  return await (await db.query(query)).all()
}

function validateVariantInput (input: paramsFormatType): void {
  if (Object.keys(input).filter(item => !['limit', 'page', 'verbose', 'organism', 'log10pvalue', 'label', 'effect_size', 'source'].includes(item)).length === 0) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one node property for variant must be defined.'
    })
  }
  if ((input.chr === undefined && input.position !== undefined) || (input.chr !== undefined && input.position === undefined)) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Chromosome and position must be defined together.'
    })
  }
}

function validateGeneInput (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['gene_id', 'hgnc', 'gene_name', 'region', 'alias'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one gene property must be defined.'
    })
  }
}

async function getVariantFromGene (input: paramsFormatType): Promise<any[]> {
  validateGeneInput(input)
  delete input.organism
  const customFilters = []

  if ('log10pvalue' in input) {
    customFilters.push(`record['log10pvalue:long'] <= ${MAX_LOG10_PVALUE}`)
    if (!(input.log10pvalue as string).includes(':')) {
      raiseInvalidParameters('log10pvalue')
    }
  }

  if ('effect_size' in input) {
    customFilters.push(`record['effect_size:long'] <= ${MAX_SLOPE}`)
    if (!(input.effect_size as string).includes(':')) {
      raiseInvalidParameters('effect_size')
    }
  }
  const { gene_id, hgnc, gene_name: name, region, alias, gene_type, organism, page } = input
  const geneInput: paramsFormatType = { gene_id, hgnc, name, region, alias, gene_type, organism, page }
  delete input.gene_id
  delete input.hgnc
  delete input.gene_name
  delete input.region
  delete input.alias
  delete input.gene_type
  delete input.organism
  const genes = await geneSearch(geneInput)
  const geneIDs = genes.map(gene => `${geneSchema.db_collection_name as string}/${gene._id as string}`)

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filterStatement = `FILTER record._to IN ['${geneIDs.join('\', \'')}'] `
  const filters = getFilterStatements(qtls, input)
  if (filters !== '') {
    filterStatement = filterStatement + ` AND ${filters}`
  }
  if (customFilters.length > 0) {
    filterStatement = filterStatement + ` AND ${customFilters.join(' AND ')}`
  }

  const sourceQuery = `FOR otherRecord IN variants
  FILTER otherRecord._id == record._from
  RETURN {${getDBReturnStatements(variantSchema).replaceAll('record', 'otherRecord')}}
  `

  const targetQuery = `FOR otherRecord IN genes
  FILTER otherRecord._id == record._to
  RETURN {${getDBReturnStatements(geneSchema).replaceAll('record', 'otherRecord')}}
  `

  const query = `
    FOR record IN variants_genes
    ${filterStatement}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN {
      ${getDBReturnStatements(qtls)},
      'sequence variant': ${input.verbose === 'true' ? `(${sourceQuery})[0]` : 'record._from'},
      'gene': ${input.verbose === 'true' ? `(${targetQuery})[0]` : 'record._to'}
    }
  `
  const cursor = await db.query(query)
  const objects = await cursor.all()

  for (let index = 0; index < objects.length; index++) {
    const element = objects[index]
    if (element.log10pvalue === MAX_LOG10_PVALUE) {
      objects[index].log10pvalue = 'inf'
    }
  }

  return objects
}

async function getGeneFromVariant (input: paramsFormatType): Promise<any[]> {
  validateVariantInput(input)
  delete input.organism
  const customFilters = []

  if ('log10pvalue' in input) {
    customFilters.push(`record['log10pvalue:long'] <= ${MAX_LOG10_PVALUE}`)
    if (!(input.log10pvalue as string).includes(':')) {
      raiseInvalidParameters('log10pvalue')
    }
  }

  if ('effect_size' in input) {
    customFilters.push(`record['effect_size:long'] <= ${MAX_SLOPE}`)
    if (!(input.effect_size as string).includes(':')) {
      raiseInvalidParameters('effect_size')
    }
  }

  // eslint-disable-next-line @typescript-eslint/naming-convention
  const variantInput: paramsFormatType = (({ variant_id, spdi, hgvs, rsid, chr, position }) => ({ variant_id, spdi, hgvs, rsid, chr, position }))(input)
  delete input.variant_id
  delete input.spdi
  delete input.hgvs
  delete input.rsid
  delete input.chr
  delete input.position
  const variantIDs = await variantIDSearch(variantInput)

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filterStatement = `FILTER record._from IN ['${variantIDs?.join('\', \'')}']`
  const filters = getFilterStatements(qtls, input)
  if (filters !== '') {
    filterStatement = filterStatement + ` AND ${filters}`
  }
  if (customFilters.length > 0) {
    filterStatement = filterStatement + ` AND ${customFilters.join(' AND ')}`
  }

  const sourceQuery = `FOR otherRecord IN variants
  FILTER otherRecord._id == record._from
  RETURN {${getDBReturnStatements(variantSchema).replaceAll('record', 'otherRecord')}}
  `

  const targetQuery = `FOR otherRecord IN genes
  FILTER otherRecord._id == record._to
  RETURN {${getDBReturnStatements(geneSchema).replaceAll('record', 'otherRecord')}}
  `

  const query = `
    FOR record IN variants_genes
    ${filterStatement}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN {
      ${getDBReturnStatements(qtls)},
      'sequence variant': ${input.verbose === 'true' ? `(${sourceQuery})[0]` : 'record._from'},
      'gene': ${input.verbose === 'true' ? `(${targetQuery})[0]` : 'record._to'}
    }
  `
  const cursor = await db.query(query)
  const objects = await cursor.all()

  for (let index = 0; index < objects.length; index++) {
    const element = objects[index]
    if (element.log10pvalue === MAX_LOG10_PVALUE) {
      objects[index].log10pvalue = 'inf'
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
    RETURN {${getDBReturnStatements(schema.gene)}}
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
      RETURN {${getDBReturnStatements(schema.gene)}}
    )

    LET RIGHT = (
      FOR record in genes
      FILTER record.chr == '${regionParams[1]}' and record['start:long'] > ${regionParams[3]}
      SORT record['start:long']
      LIMIT 1
      RETURN {${getDBReturnStatements(schema.gene)}}
    )

    RETURN UNION(LEFT, RIGHT)
  `

  const nearestGenes = await (await db.query(nearestQuery)).all()
  if (nearestGenes !== undefined) {
    return nearestGenes[0]
  }

  return []
}

const genesFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/genes', description: descriptions.variants_genes } })
  .input(variantsCommonQueryFormat.merge(variantsGenesQueryFormat).merge(commonHumanEdgeParamsFormat))
  .output(z.array(eqtlFormat.merge(sqtlFormat)))
  .query(async ({ input }) => await getGeneFromVariant(input))

const variantsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/variants', description: descriptions.genes_variants } })
  .input(geneQueryFormat)
  .output(z.array(eqtlFormat))
  .query(async ({ input }) => await getVariantFromGene(input))

const nearestGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/nearest-genes', description: descriptions.nearest_genes } })
  .input(z.object({ region: z.string().trim() }))
  .output(z.array(geneFormat))
  .query(async ({ input }) => await nearestGeneSearch(input))

const qtlSummaryEndpoint = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/genes/summary', description: descriptions.variants_genes_summary } })
  .input(singleVariantQueryFormat)
  .output(z.array(qtlsSummaryFormat))
  .query(async ({ input }) => await qtlSummary(input))

export const variantsGenesRouters = {
  qtlSummaryEndpoint,
  genesFromVariants,
  variantsFromGenes,
  nearestGenes
}
