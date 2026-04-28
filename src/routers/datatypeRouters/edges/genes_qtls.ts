import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { geneSearch } from '../nodes/genes'
import { paramsFormatType } from '../_helpers'
import { TRPCError } from '@trpc/server'
import { descriptions } from '../descriptions'
import { commonHumanEdgeParamsFormat } from '../params'

const MAX_PAGE_SIZE = 100

const variantReturnFormat = z.object({
  chr: z.string(),
  pos: z.number(),
  SPDI: z.string().nullish(),
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
  nLog10Pvalue: z.number().nullish(),
  effect_size: z.number().nullish(),
  posterior_inclusion_probability: z.number().nullish(), // EBI eQTL and spliceQTL only
  intron_chr: z.string().nullish(), // spliceQTL only
  intron_start: z.union([z.string(), z.number()]).nullish(), // spliceQTL only
  intron_end: z.union([z.string(), z.number()]).nullish(), // spliceQTL only
  study: z.string().nullish() // EBI eQTL and spliceQTL only
})

const SOURCES = z.enum(['AFGRS', 'EBI', 'IGVF', 'ENCODE', 'UKB'])
const METHODS = z.enum(['eQTL', 'pQTL', 'spliceQTL', 'caQTL'])

const geneQuery = z.object({
  gene_id: z.string().trim().optional(),
  gene_name: z.string().trim().optional(),
  biological_context: z.string().trim().optional(),
  method: METHODS.optional(),
  source: SOURCES.optional()
}).merge(commonHumanEdgeParamsFormat).omit({ verbose: true })

function validateGeneInput (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['gene_id', 'gene_name'].includes(item) || input[item] === undefined)
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one gene property must be defined.'
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

function qtlReturnObject (genomicElementExpr: string): string {
  return `{
    _key: record._key,
    variant: { chr: variant.chr, pos: variant.pos, SPDI: variant.spdi, rsid: variant.rsid },
    gene: { name: geneRecord.name, id: geneRecord._key },
    genomic_element: ${genomicElementExpr},
    source: record.source,
    method: record.method,
    regulatory_type: record.regulatory_type,
    gene_consequence: record.gene_consequence,
    biological_context: record.biological_context,
    nLog10Pvalue: record.log10pvalue,
    effect_size: HAS(record, 'effect_size') ? record.effect_size : record.beta,
    posterior_inclusion_probability: record.posterior_inclusion_probability,
    intron_chr: record.intron_chr,
    intron_start: record.intron_start,
    intron_end: record.intron_end,
    study: record.study
  }`
}

function variantsGenesQuery (filterClause: string, withLimit: boolean): string {
  return `
  FOR record IN variants_genes
  FILTER record._to == @geneID ${filterClause}
  LET variant = DOCUMENT(record._from)
  LET geneRecord = DOCUMENT(record._to)
  SORT record._key
  ${withLimit ? 'LIMIT @offset, @limit' : ''}
  RETURN ${qtlReturnObject('null')}
  `
}

function variantsProteinsQuery (filterClause: string, withLimit: boolean): string {
  return `
  FOR record IN variants_proteins
  FILTER record.gene == @geneID ${filterClause}
  LET variant = DOCUMENT(record._from)
  LET geneRecord = DOCUMENT(record.gene)
  SORT record._key
  ${withLimit ? 'LIMIT @offset, @limit' : ''}
  RETURN ${qtlReturnObject('null')}
  `
}

function variantsGenomicElementsQuery (filterClause: string, withLimit: boolean): string {
  return `
  LET geneRecord = DOCUMENT(@geneID)
  FILTER geneRecord != null
  LET genomicElementIDs = (
    FOR ge IN genomic_elements
    FILTER ge.chr == geneRecord.chr
      AND ge.end >= geneRecord.start
      AND ge.start <= geneRecord.end
    RETURN ge._id
  )
  FOR record IN variants_genomic_elements
  FILTER record._to IN genomicElementIDs ${filterClause}
  LET variant = DOCUMENT(record._from)
  LET genomicElement = DOCUMENT(record._to)
  SORT record._key
  ${withLimit ? 'LIMIT @offset, @limit' : ''}
  RETURN ${qtlReturnObject(
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
  const { gene_id, gene_name, organism } = input
  const geneInput: paramsFormatType = { gene_id, name: gene_name, organism, page: 0 }
  delete input.gene_id
  delete input.gene_name
  delete input.organism

  const genes = await geneSearch(geneInput)
  const geneIDs = genes.map(gene => `genes/${gene._id as string}`)
  if (geneIDs.length === 0) {
    return []
  }
  const geneID = geneIDs[0]

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  const page = (input.page as number) ?? 0
  const offset = page * limit

  const { filterClause, bindVars } = getFilterClauseAndBindVars(input)
  const baseBindVars = { geneID, offset, limit, ...bindVars }

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

const qtlsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/qtls', description: descriptions.genes_qtls } })
  .input(geneQuery)
  .output(z.array(outputFormat))
  .query(async ({ input }) => await qtlsFromGeneSearch(input))

export const genesQTLsRouters = {
  qtlsFromGenes
}
