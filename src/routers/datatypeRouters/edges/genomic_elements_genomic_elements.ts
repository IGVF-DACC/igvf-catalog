import { z } from 'zod'
import { TRPCError } from '@trpc/server'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { commonHumanEdgeParamsFormat } from '../params'
import { getFilterStatements, preProcessRegionParam } from '../_helpers'
import { getCollectionEnumValuesOrThrow, getSchema } from '../schema'
import { descriptions } from '../descriptions'

const collection = 'genomic_elements_genomic_elements'
const edgeSchema = getSchema('data/schemas/edges/genomic_elements_genomic_elements.CRISPRElementElement.json')
const elementSchema = getSchema('data/schemas/nodes/genomic_elements.CRISPRElementElement.json')
const textFilter = z.string().trim().min(1).optional()
const inputFormat = commonHumanEdgeParamsFormat.extend({
  source_element_id: textFilter,
  target_element_id: textFilter,
  source_region: textFilter,
  target_region: textFilter,
  promoter_gene_id: textFilter,
  files_fileset: textFilter,
  biosample_term: textFilter,
  biological_context: textFilter,
  method: z.enum(getCollectionEnumValuesOrThrow('edges', collection, 'method')).optional(),
  source: z.enum(getCollectionEnumValuesOrThrow('edges', collection, 'source')).optional(),
  crispr_modality: z.enum(getCollectionEnumValuesOrThrow('edges', collection, 'crispr_modality')).optional(),
  significant: z.enum(['true', 'false']).optional(),
  log2FC: textFilter,
  p_value: textFilter,
  p_value_adj: textFilter,
  neg_log10_pvalue: textFilter,
  neg_log10_pvalue_adj: textFilter,
  page: z.number().int().nonnegative().default(0),
  limit: z.number().int().positive().optional()
})
const elementFormat = z.object({
  _id: z.string(),
  name: z.string(),
  chr: z.string(),
  start: z.number(),
  end: z.number(),
  type: z.string().nullish(),
  source_annotation: z.string().nullish(),
  promoter_of: z.string().nullish()
})
const outputFormat = z.array(z.object({
  source_genomic_element: z.string().or(elementFormat),
  target_genomic_element: z.string().or(elementFormat),
  name: z.string(),
  inverse_name: z.string(),
  label: z.string(),
  class: z.string(),
  method: z.string(),
  source: z.string(),
  source_url: z.string(),
  files_filesets: z.string(),
  biological_context: z.string().nullish(),
  biosample_term: z.string().nullish(),
  treatments_term_ids: z.array(z.string()).nullish(),
  crispr_modality: z.string().nullish(),
  log2FC: z.number().nullish(),
  p_value: z.number().nullish(),
  p_value_adj: z.number().nullish(),
  neg_log10_pvalue: z.number().nullish(),
  neg_log10_pvalue_adj: z.number().nullish(),
  significant: z.boolean().nullish()
}))

const handle = (collection: string, value: string): string => value.startsWith(`${collection}/`) ? value : `${collection}/${value}`

const genomicElementsFromGenomicElements = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genomic-elements/genomic-elements', description: descriptions.genomic_elements_genomic_elements } })
  .input(inputFormat)
  .output(outputFormat)
  .query(async ({ input }) => {
    if (![input.source_element_id, input.target_element_id, input.source_region, input.target_region, input.promoter_gene_id, input.files_fileset, input.method].some(value => value !== undefined)) {
      throw new TRPCError({ code: 'BAD_REQUEST', message: 'Define at least one source_element_id, target_element_id, source_region, target_region, promoter_gene_id, files_fileset, or method.' })
    }
    const filters: string[] = []
    const bindVars: Record<string, unknown> = {
      offset: input.page * Math.min(input.limit ?? QUERY_LIMIT, 500),
      limit: Math.min(input.limit ?? QUERY_LIMIT, 500)
    }
    const equalityFilters = {
      _from: input.source_element_id === undefined ? undefined : handle('genomic_elements', input.source_element_id),
      _to: input.target_element_id === undefined ? undefined : handle('genomic_elements', input.target_element_id),
      files_filesets: input.files_fileset === undefined ? undefined : handle('files_filesets', input.files_fileset),
      biosample_term: input.biosample_term === undefined ? undefined : handle('ontology_terms', input.biosample_term),
      biological_context: input.biological_context,
      method: input.method,
      source: input.source,
      crispr_modality: input.crispr_modality,
      significant: input.significant === undefined ? undefined : input.significant === 'true'
    }
    for (const [field, value] of Object.entries(equalityFilters)) {
      if (value !== undefined) {
        filters.push(`record.${field} == @${field}`)
        bindVars[field] = value
      }
    }
    const metrics = getFilterStatements(edgeSchema, {
      log2FC: input.log2FC,
      p_value: input.p_value,
      p_value_adj: input.p_value_adj,
      neg_log10_pvalue: input.neg_log10_pvalue,
      neg_log10_pvalue_adj: input.neg_log10_pvalue_adj
    })
    if (metrics !== '') filters.push(metrics)
    // Region and promoter-gene filters act on the nodes, before edge pagination.
    const nodeQueries: string[] = []
    for (const [side, region, endpoint] of [['source', input.source_region, '_from'], ['target', input.target_region, '_to']] as const) {
      const nodeFilters: string[] = []
      if (region !== undefined) nodeFilters.push(getFilterStatements(elementSchema, preProcessRegionParam({ region })))
      if (side === 'source' && input.promoter_gene_id !== undefined) {
        nodeFilters.push('record.promoter_of == @promoterGene')
        bindVars.promoterGene = handle('genes', input.promoter_gene_id)
      }
      if (nodeFilters.length > 0) {
        nodeQueries.push(`LET ${side}IDs = (FOR record IN genomic_elements FILTER ${nodeFilters.join(' AND ')} RETURN record._id)`)
        filters.push(`record.${endpoint} IN ${side}IDs`)
      }
    }
    const expanded = (endpoint: string): string => input.verbose === 'true'
      ? `KEEP(DOCUMENT(record.${endpoint}), '_id', 'name', 'chr', 'start', 'end', 'type', 'source_annotation', 'promoter_of')`
      : `record.${endpoint}`
    const fields = Object.keys(outputFormat.element.shape).filter(field => !['source_genomic_element', 'target_genomic_element'].includes(field))
    const cursor = await db.query(`
      ${nodeQueries.join('\n')}
      FOR record IN ${collection}
        FILTER ${filters.join(' AND ') || 'true'}
        SORT record._key
        LIMIT @offset, @limit
        RETURN {
          source_genomic_element: ${expanded('_from')},
          target_genomic_element: ${expanded('_to')},
          ${fields.map(field => `${field}: record.${field}`).join(',\n')}
        }
    `, bindVars)
    return await cursor.all()
  })

export const genomicElementsGenomicElementsRouters = { genomicElementsFromGenomicElements }
