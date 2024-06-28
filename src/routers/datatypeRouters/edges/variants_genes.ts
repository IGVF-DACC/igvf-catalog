import { z } from 'zod'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam, validRegion } from '../_helpers'
import { QUERY_LIMIT } from '../../../constants'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { geneFormat } from '../nodes/genes'
import { variantFormat, variantIDSearch } from '../nodes/variants'
import { commonHumanEdgeParamsFormat, variantsHumanCommonQueryFormat } from '../params'

// not sure how to set this number //
const MAX_PAGE_SIZE = 500

// Values calculated from database to optimize range queries
// MAX pvalue = 0.00175877, MAX -log10 pvalue = 306.99234812274665 (from datasets)
const MAX_LOG10_PVALUE = 400
const MAX_SLOPE = 8.66426 // i.e. effect_size

const schema = loadSchemaConfig()

const QtlSources = z.enum(['GTEx', 'AFGR'])

const variantsGenesQueryFormat = z.object({
  log10pvalue: z.string().trim().optional(),
  effect_size: z.string().optional(),
  label: z.enum(['eQTL', 'splice_QTL']).optional(),
  source: QtlSources.optional()
})

const geneQueryFormat = z.object({
  gene_id: z.string().trim().optional()
}).merge(variantsGenesQueryFormat).merge(commonHumanEdgeParamsFormat)

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

function validateInput (input: paramsFormatType): void {
  if (Object.keys(input).filter(item => !['limit', 'page', 'verbose', 'organism', 'log10pvalue', 'label', 'effect_size', 'source'].includes(item)).length === 0) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one node property for variant / gene must be defined.'
    })
  }
  if ((input.chr === undefined && input.position !== undefined) || (input.chr !== undefined && input.position === undefined)) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Chromosome and position must be defined together.'
    })
  }
}

async function qtlSearch (input: paramsFormatType): Promise<any[]> {
  validateInput(input)
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

  let filterStatement = ''
  if ('gene_id' in input) {
    filterStatement = `FILTER record._to == 'genes/${input.gene_id as string}'`
    delete input.gene_id
  } else if (variantIDs !== undefined) {
    filterStatement = `FILTER record._from IN ['${variantIDs?.join('\', \'')}']`
  }
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
  .input(variantsHumanCommonQueryFormat.merge(variantsGenesQueryFormat).merge(commonHumanEdgeParamsFormat))
  .output(z.array(eqtlFormat.merge(sqtlFormat)))
  .query(async ({ input }) => await qtlSearch(input))

const variantsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/variants', description: descriptions.genes_variants } })
  .input(geneQueryFormat)
  .output(z.array(eqtlFormat))
  .query(async ({ input }) => await qtlSearch(input))

const nearestGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/nearest-genes', description: descriptions.nearest_genes } })
  .input(z.object({ region: z.string().trim() }))
  .output(z.array(geneFormat))
  .query(async ({ input }) => await nearestGeneSearch(input))

export const variantsGenesRouters = {
  genesFromVariants,
  variantsFromGenes,
  nearestGenes
}
