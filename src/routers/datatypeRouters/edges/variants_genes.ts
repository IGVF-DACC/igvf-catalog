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
import { studyFormat } from '../nodes/studies'

const MAX_PAGE_SIZE = 500

// Values calculated from database to optimize range queries
// MAX pvalue = 0.00175877, MAX -log10 pvalue = 306.99234812274665 (from datasets)
const MAX_LOG10_PVALUE = 400
const MAX_SLOPE = 8.66426 // i.e. effect_size

const schema = loadSchemaConfig()

const QtlSources = z.enum([
  'AFGR',
  'eQTL Catalogue',
  'IGVF'
])

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
  }).nullish(),
  name: z.string().nullish()
})

const variantsGenesQueryFormat = z.object({
  log10pvalue: z.string().trim().optional(),
  effect_size: z.string().optional(),
  label: z.enum(['eQTL', 'splice_QTL', 'variant effect on gene expression of ENSG00000108179', 'variant effect on gene expression of ENSG00000134460']).optional(),
  source: QtlSources.optional(),
  name: z.enum(['modulates expression of', 'modulates splicing of']).optional()
})

const geneQueryFormat = genesCommonQueryFormat.merge(variantsGenesQueryFormat).merge(commonHumanEdgeParamsFormat).merge(z.object({
  // use inverse name value here
  name: z.enum(['expression modulated by', 'splicing modulated by']).optional()
}))

const simplifiedQtlFormat = z.object({
  sequence_variant: z.string().or(variantFormat).nullable(),
  gene: z.string().or(geneFormat).nullable(),
  study: z.string().or(studyFormat).nullable(),
  label: z.string(),
  log10pvalue: z.number().or(z.string()).nullable(),
  effect_size: z.number().nullable(),
  method: z.string().nullable(),
  source: z.string(),
  source_url: z.string().optional(),
  biological_context: z.string().or(z.array(z.string())),
  chr: z.string().nullable(),
  name: z.string().nullish()
})

const completeQtlsFormat = z.object({
  intron_chr: z.string().nullable(),
  intron_start: z.string().nullable(),
  intron_end: z.string().nullable(),
  effect_size: z.number().nullable(),
  log10pvalue: z.number().nullable(),
  pval_beta: z.number().nullable(),
  method: z.string().nullable(),
  source: z.string(),
  source_url: z.string(),
  label: z.string(),
  p_value: z.number().nullable(),
  chr: z.string().nullable(),
  biological_context: z.string().or(z.array(z.string())),
  sequence_variant: z.string().or(variantFormat).nullable(),
  study: z.string().or(studyFormat).nullable(),
  gene: z.string().or(geneFormat).nullable(),
  name: z.string().nullish()
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

  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = ` AND record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
    delete input.files_fileset
  }

  const targetQuery = `FOR otherRecord IN genes
  FILTER otherRecord._id == record._to
  RETURN {
    gene_name: otherRecord.name,
    gene_id: otherRecord._key,
    gene_start: otherRecord.start,
    gene_end: otherRecord.end,
  }
  `

  const query = `
    FOR record IN variants_genes
    FILTER record._from == 'variants/${variant[0]._id as string}' ${filesetFilter}
    RETURN {
      qtl_type: record.label,
      log10pvalue: record.log10pvalue,
      chr: record.chr OR SPLIT(record.variant_chromosome_position_ref_alt, '_')[0],
      biological_context: record.biological_context,
      effect_size: record.effect_size,
      pval_beta: record.pval_beta or record.beta,
      'gene': (${targetQuery})[0],
      'name': record.name
    }
  `

  return await (await db.query(query)).all()
}

function validateVariantInput (input: paramsFormatType): void {
  if (Object.keys(input).filter(item => !['name', 'limit', 'page', 'verbose', 'organism', 'log10pvalue', 'label', 'effect_size', 'source'].includes(item)).length === 0) {
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
  const isInvalidFilter = Object.keys(input).every(item => !['gene_id', 'hgnc_id', 'gene_name', 'region', 'alias'].includes(item))
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
    customFilters.push(`record.log10pvalue <= ${MAX_LOG10_PVALUE}`)
    if (!(input.log10pvalue as string).includes(':')) {
      raiseInvalidParameters('log10pvalue')
    }
  }

  if ('effect_size' in input) {
    customFilters.push(`record.effect_size <= ${MAX_SLOPE}`)
    if (!(input.effect_size as string).includes(':')) {
      raiseInvalidParameters('effect_size')
    }
  }
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { gene_id, hgnc_id, gene_name: name, alias, organism } = input
  const geneInput: paramsFormatType = { gene_id, hgnc_id, name, alias, organism, page: 0 }
  delete input.gene_id
  delete input.hgnc_id
  delete input.gene_name
  delete input.alias
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

  const studyQuery = `
    FOR studyRecord IN studies
    FILTER studyRecord._id == record.study
    RETURN {${getDBReturnStatements(schema.study).replaceAll('record', 'studyRecord')}}
  `

  const query = `
    FOR record IN variants_genes
    ${filterStatement}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN {
      'effect_size': record['effect_size'], 'log10pvalue': record['log10pvalue'], 'source': record['source'], 'label': record['label'], 'chr': record['chr'], 'source_url': record['source_url'], 'biological_context': record['biological_context'], 'method': record['method'],
      'study': ${input.verbose === 'true' ? `(${studyQuery})[0]` : 'record.study'},
      'sequence_variant': ${input.verbose === 'true' ? `(${sourceQuery})[0]` : 'record._from'},
      'gene': ${input.verbose === 'true' ? `(${targetQuery})[0]` : 'record._to'},
      'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
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
    customFilters.push(`record.log10pvalue <= ${MAX_LOG10_PVALUE}`)
    if (!(input.log10pvalue as string).includes(':')) {
      raiseInvalidParameters('log10pvalue')
    }
  }

  if ('effect_size' in input) {
    customFilters.push(`record.effect_size <= ${MAX_SLOPE}`)
    if (!(input.effect_size as string).includes(':')) {
      raiseInvalidParameters('effect_size')
    }
  }

  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = ` AND record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
    delete input.files_fileset
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

  const studyQuery = `
    FOR studyRecord IN studies
    FILTER studyRecord._id == record.study
    RETURN {${getDBReturnStatements(schema.study).replaceAll('record', 'studyRecord')}}
  `

  const query = `
    FOR record IN variants_genes
    ${filterStatement} ${filesetFilter}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN {
      'intron_chr': record['intron_chr'], 'intron_start': record['intron_start'], 'intron_end': record['intron_end'], 'effect_size': record['effect_size'], 'log10pvalue': record['log10pvalue'], 'pval_beta': record['pval_beta'], 'source': record['source'], 'label': record['label'], 'p_value': record['p_value'], 'chr': record['chr'], 'source_url': record['source_url'], 'biological_context': record['biological_context'], 'method': record['method'],
      'study': ${input.verbose === 'true' ? `(${studyQuery})[0]` : 'record.study'},
      'sequence_variant': ${input.verbose === 'true' ? `(${sourceQuery})[0]` : 'record._from'},
      'gene': ${input.verbose === 'true' ? `(${targetQuery})[0]` : 'record._to'},
      'name': record.name
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
      FILTER record.chr == '${regionParams[1]}' and record.end < ${regionParams[2]}
      SORT record.end DESC
      LIMIT 1
      RETURN {${getDBReturnStatements(schema.gene)}}
    )

    LET RIGHT = (
      FOR record in genes
      FILTER record.chr == '${regionParams[1]}' and record.start > ${regionParams[3]}
      SORT record.start
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
  .input(variantsCommonQueryFormat.merge(z.object({ files_fileset: z.string().optional() })).merge(variantsGenesQueryFormat).merge(commonHumanEdgeParamsFormat))
  .output(z.array(completeQtlsFormat))
  .query(async ({ input }) => await getGeneFromVariant(input))

const variantsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/variants', description: descriptions.genes_variants } })
  .input(geneQueryFormat)
  .output(z.array(simplifiedQtlFormat))
  .query(async ({ input }) => await getVariantFromGene(input))

const nearestGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/nearest-genes', description: descriptions.nearest_genes } })
  .input(z.object({ region: z.string().trim() }))
  .output(z.array(geneFormat))
  .query(async ({ input }) => await nearestGeneSearch(input))

const qtlSummaryEndpoint = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/genes/summary', description: descriptions.variants_genes_summary } })
  .input(singleVariantQueryFormat.merge(z.object({ files_fileset: z.string().optional() })))
  .output(z.array(qtlsSummaryFormat))
  .query(async ({ input }) => await qtlSummary(input))

export const variantsGenesRouters = {
  qtlSummaryEndpoint,
  genesFromVariants,
  variantsFromGenes,
  nearestGenes
}
