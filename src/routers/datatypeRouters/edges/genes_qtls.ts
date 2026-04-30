import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { geneSearch } from '../nodes/genes'
import { paramsFormatType } from '../_helpers'
import { TRPCError } from '@trpc/server'
import { descriptions } from '../descriptions'
import { commonHumanEdgeParamsFormat } from '../params'
import { variantSearch } from '../nodes/variants'

const MAX_PAGE_SIZE = 100

const variantReturnFormat = z.object({
  chr: z.string(),
  pos: z.number(),
  spdi: z.string().nullish(),
  rsid: z.union([z.string(), z.array(z.string())]).nullish()
})

const outputFormat = z.object({
  variant: variantReturnFormat,
  gene: z.object({
    name: z.string(),
    id: z.string()
  }).nullable(),
  genomic_element: z.object({
    name: z.string(),
    chr: z.string(),
    start: z.number(),
    stop: z.number(),
    type: z.string()
  }).nullable(),
  source: z.string(),
  method: z.string(),
  regulatory_type: z.string().nullish(), // pQTL only
  gene_consequence: z.string().nullish(), // pQTL only
  biological_context: z.string().nullish(),
  neg_log10_pvalue: z.number().nullish(),
  effect_size: z.number().nullish(),
  posterior_inclusion_probability: z.number().nullish(), // EBI eQTL and spliceQTL only
  intron_chr: z.string().nullish(), // spliceQTL only
  intron_start: z.union([z.string(), z.number()]).nullish(), // spliceQTL only
  intron_end: z.union([z.string(), z.number()]).nullish(), // spliceQTL only
  study: z.string().nullish(), // EBI eQTL and spliceQTL only
  files_filesets: z.string().nullish()
})

const SOURCES = z.enum(['AFGRS', 'EBI', 'IGVF', 'ENCODE', 'UKB'])
const METHODS = z.enum(['eQTL', 'pQTL', 'spliceQTL', 'caQTL'])

const geneQuery = z.object({
  gene_id: z.string().trim().optional(),
  gene_name: z.string().trim().optional(),
  region: z.string().trim().optional(),
  biological_context: z.string().trim().optional(),
  method: METHODS.optional(),
  source: SOURCES.optional()
}).merge(commonHumanEdgeParamsFormat).omit({ verbose: true })

const variantQuery = z.object({
  variant_id: z.string().trim().optional(),
  spdi: z.string().trim().optional(),
  rsid: z.string().trim().optional(),
  ca_id: z.string().trim().optional(),
  region: z.string().trim().optional(),
  biological_context: z.string().trim().optional(),
  method: METHODS.optional(),
  source: SOURCES.optional()
}).merge(commonHumanEdgeParamsFormat).omit({ verbose: true })

function validateGeneInput (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['gene_id', 'gene_name', 'region'].includes(item) || input[item] === undefined)
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one gene property must be defined.'
    })
  }
}

function validateVariantInput (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['variant_id', 'spdi', 'rsid', 'ca_id', 'region'].includes(item) || input[item] === undefined)
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one variant property must be defined.'
    })
  }
}
function getFilterClauseAndBindVars (input: paramsFormatType): { filterClause: string, bindVars: Record<string, unknown> } {
  const clauses: string[] = []
  const bindVars: Record<string, unknown> = {}

  if (input.biological_context !== undefined) {
    clauses.push('record.biological_context == @biological_context')
    bindVars.biological_context = input.biological_context
  }
  if (input.method !== undefined) {
    clauses.push('record.method == @method')
    bindVars.method = input.method
  }
  if (input.source !== undefined) {
    clauses.push('record.source == @source')
    bindVars.source = input.source
  }

  return {
    filterClause: clauses.length > 0 ? `AND ${clauses.join(' AND ')}` : '',
    bindVars
  }
}

function qtlReturnObject (geneExpr: string, genomicElementExpr: string): string {
  return `{
    _key: record._key,
    variant: { chr: variant.chr, pos: variant.pos, spdi: variant.spdi, rsid: variant.rsid },
    gene: ${geneExpr},
    genomic_element: ${genomicElementExpr},
    source: record.source,
    method: record.method,
    regulatory_type: record.regulatory_type,
    gene_consequence: record.gene_consequence,
    biological_context: record.biological_context,
    neg_log10_pvalue: record.log10pvalue,
    effect_size: HAS(record, 'effect_size') ? record.effect_size : record.beta,
    posterior_inclusion_probability: record.posterior_inclusion_probability,
    intron_chr: record.intron_chr,
    intron_start: record.intron_start,
    intron_end: record.intron_end,
    study: record.study,
    files_filesets: record.files_filesets
  }`
}

function variantsGenesQuery (filterClause: string, withLimit: boolean): string {
  return `
  FOR record IN variants_genes
  FILTER record._to IN @geneIDs ${filterClause}
  SORT record._key
  ${withLimit ? 'LIMIT @offset, @limit' : ''}
  LET variant = DOCUMENT(record._from)
  LET geneRecord = DOCUMENT(record._to)
  RETURN ${qtlReturnObject('{ name: geneRecord.name, id: geneRecord._key }', 'null')}
  `
}

function variantsProteinsQuery (filterClause: string, withLimit: boolean): string {
  return `
  FOR record IN variants_proteins
  FILTER record.gene IN @geneIDs ${filterClause}
  SORT record._key
  ${withLimit ? 'LIMIT @offset, @limit' : ''}
  LET variant = DOCUMENT(record._from)
  LET geneRecord = DOCUMENT(record.gene)
  RETURN ${qtlReturnObject('{ name: geneRecord.name, id: geneRecord._key }', 'null')}
  `
}

function variantsGenomicElementsQuery (filterClause: string, withLimit: boolean): string {
  return `
  LET genomicElementGenePairs = (
    FOR g IN @geneIDs
      LET geneRecord = DOCUMENT(g)
      FILTER geneRecord != null
      FOR ge IN genomic_elements
      FILTER ge.chr == geneRecord.chr
        AND ge.end >= geneRecord.start
        AND ge.start < geneRecord.end
      COLLECT element_id = ge._id INTO grouped = g
      RETURN { element_id: element_id, gene_id: FIRST(grouped) }
  )
  LET genomicElementIDs = genomicElementGenePairs[*].element_id
  FOR record IN variants_genomic_elements
  FILTER record._to IN genomicElementIDs ${filterClause}
  SORT record._key
  ${withLimit ? 'LIMIT @offset, @limit' : ''}
  LET variant = DOCUMENT(record._from)
  LET genomicElement = DOCUMENT(record._to)
  LET geneID = FIRST(
    FOR pair IN genomicElementGenePairs
    FILTER pair.element_id == record._to
    RETURN pair.gene_id
  )
  LET geneRecord = DOCUMENT(geneID)
  FILTER geneRecord != null
  RETURN ${qtlReturnObject(
      '{ name: geneRecord.name, id: geneRecord._key }',
      `{
      name: genomicElement.name,
      chr: genomicElement.chr,
      start: genomicElement.start,
      stop: genomicElement.end,
      type: genomicElement.type
    }`
    )}
  `
}

async function qtlsFromGeneSearch (input: paramsFormatType): Promise<any[]> {
  validateGeneInput(input)
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { gene_id, gene_name, region, organism } = input
  const geneInput: paramsFormatType = { gene_id, name: gene_name, region, organism, page: 0 }
  delete input.gene_id
  delete input.gene_name
  delete input.region
  delete input.organism

  const genes = await geneSearch(geneInput)
  const geneIDs = genes.map(gene => `genes/${gene._id as string}`)
  if (geneIDs.length === 0) {
    return []
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  const page = (input.page as number) ?? 0
  const offset = page * limit

  const { filterClause, bindVars } = getFilterClauseAndBindVars(input)
  const baseBindVars = { geneIDs, offset, limit, ...bindVars }

  if (input.method !== undefined) {
    if (input.method === 'eQTL' || input.method === 'spliceQTL') {
      if (input.source !== undefined && !['AFGR', 'EBI'].includes(input.source as string)) {
        return []
      }
      return await (await db.query(variantsGenesQuery(filterClause, true), baseBindVars)).all()
    } else if (input.method === 'pQTL') {
      if (input.source !== undefined && input.source !== 'UKB') {
        return []
      }
      return await (await db.query(variantsProteinsQuery(filterClause, true), baseBindVars)).all()
    } else if (input.method === 'caQTL') {
      if (input.source !== undefined && !['AFGR', 'ENCODE'].includes(input.source as string)) {
        return []
      }
      return await (await db.query(variantsGenomicElementsQuery(filterClause, true), baseBindVars)).all()
    }
    return []
  }

  const allQTLsQuery = `
  LET variantsGenes = (${variantsGenesQuery(filterClause, false)})
  LET variantsProteins = (${variantsProteinsQuery(filterClause, false)})
  LET variantsGenomicElements = (${variantsGenomicElementsQuery(filterClause, false)})
  FOR record IN UNION(variantsGenes, variantsProteins, variantsGenomicElements)
    SORT record._key ASC
    LIMIT @offset, @limit
    RETURN record
  `
  return await (await db.query(allQTLsQuery, baseBindVars)).all()
}

async function qtlsFromVariantSearch (input: paramsFormatType): Promise<any[]> {
  validateVariantInput(input)
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { variant_id, spdi, rsid, ca_id, region, organism } = input
  const variantInput: paramsFormatType = { variant_id, spdi, rsid, ca_id, region, organism, page: 0 }
  delete input.variant_id
  delete input.spdi
  delete input.rsid
  delete input.ca_id
  delete input.region
  delete input.organism
  const variants = await variantSearch(variantInput)
  const variantIDs = variants.map(variant => `variants/${variant._id as string}`)
  if (variantIDs.length === 0) {
    return []
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  const page = (input.page as number) ?? 0
  const offset = page * limit

  const { filterClause, bindVars } = getFilterClauseAndBindVars(input)
  const baseBindVars = { variantIDs, offset, limit, ...bindVars }

  const query = `
    LET variantsGenes = (
      FOR record IN variants_genes
      FILTER record._from IN @variantIDs AND record.method in ['eQTL', 'spliceQTL'] ${filterClause}
      LET variant = DOCUMENT(record._from)
      FILTER variant != null
      LET geneRecord = DOCUMENT(record._to)
      FILTER geneRecord != null
      RETURN ${qtlReturnObject('{ name: geneRecord.name, id: geneRecord._key }', 'null')}
    )
    LET variantsProteins = (
      FOR record IN variants_proteins
      FILTER record._from IN @variantIDs AND record.method == 'pQTL' ${filterClause}
      LET variant = DOCUMENT(record._from)
      FILTER variant != null
      LET geneRecord = DOCUMENT(record.gene)
      FILTER geneRecord != null
      RETURN ${qtlReturnObject('{ name: geneRecord.name, id: geneRecord._key }', 'null')}
    )
    LET variantsGenomicElements = (
      FOR record IN variants_genomic_elements
      FILTER record._from IN @variantIDs AND record.method == 'caQTL' ${filterClause}
      LET variant = DOCUMENT(record._from)
      FILTER variant != null
      LET genomicElementRecord = DOCUMENT(record._to)
      FILTER genomicElementRecord != null
      LET geneRecord = FIRST(
        FOR g IN genes
        FILTER g.chr == variant.chr
          AND g.end >= variant.pos
          AND g.start < variant.pos
        SORT g._key
        LIMIT 1
        RETURN g
      )
      RETURN ${qtlReturnObject('geneRecord == null ? null : { name: geneRecord.name, id: geneRecord._key }', '{ name: genomicElementRecord.name, chr: genomicElementRecord.chr, start: genomicElementRecord.start, stop: genomicElementRecord.end, type: genomicElementRecord.type }')}
    )
    FOR record IN UNION(variantsGenes, variantsProteins, variantsGenomicElements)
    SORT record._key ASC
    LIMIT @offset, @limit
    RETURN record
  `
  return await (await db.query(query, baseBindVars)).all()
}

const qtlsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/qtls', description: descriptions.genes_qtls } })
  .input(geneQuery)
  .output(z.array(outputFormat))
  .query(async ({ input }) => await qtlsFromGeneSearch(input))

const qtlsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/qtls', description: descriptions.variants_qtls } })
  .input(variantQuery)
  .output(z.array(outputFormat))
  .query(async ({ input }) => await qtlsFromVariantSearch(input))

export const genesQTLsRouters = {
  qtlsFromGenes,
  qtlsFromVariants
}
