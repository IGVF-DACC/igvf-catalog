import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { variantSearch, singleVariantQueryFormat, variantSimplifiedFormat } from '../nodes/variants'
import { commonHumanEdgeParamsFormat } from '../params'

const MAX_PAGE_SIZE = 100
const DISTANCE_TO_TSS_BP = 2_000_000
const OVERLAPPING_ELEMENT_METHOD = 'Perturb-seq'

const VARIANT_QUERY_KEYS = ['spdi', 'hgvs', 'ca_id', 'variant_id'] as const

const geneOutputFormat = z.object({
  _id: z.string(),
  name: z.string(),
  chr: z.string(),
  start: z.number(),
  end: z.number(),
  strand: z.string().nullish()
})

const genomicElementOutputFormat = z.object({
  _id: z.string(),
  name: z.string(),
  chr: z.string(),
  start: z.number(),
  end: z.number(),
  type: z.string().nullish(),
  source: z.string().nullish(),
  source_url: z.string().nullish()
})

const outputFormat = z.array(z.object({
  variant: variantSimplifiedFormat,
  distance_to_tss: z.number().nullish(),
  genomic_element: genomicElementOutputFormat,
  gene: geneOutputFormat,
  name: z.string(),
  label: z.string(),
  method: z.string(),
  class: z.string(),
  source: z.string(),
  source_url: z.string(),
  files_filesets: z.string(),
  biological_context: z.string(),
  biosample_term: z.string(),
  crispr_modality: z.string().nullish(),
  log2FC: z.number().nullish(),
  neg_log10_pvalue: z.number().nullish(),
  neg_log10_pvalue_adj: z.number().or(z.string()).nullish(),
  p_value: z.number().or(z.string()).nullish(),
  p_value_adj: z.number().or(z.string()).nullish(),
  effect_size: z.number().nullish(),
  significant: z.boolean().nullish()
}))

const inputFormat = singleVariantQueryFormat.omit({ organism: true }).merge(z.object({
  files_fileset: z.string().optional(),
  biosample_term: z.string().optional(),
  biological_context: z.string().optional(),
  nearby_genes: z.enum(['true', 'false']).default('true')
})).merge(commonHumanEdgeParamsFormat).omit({ verbose: true })

function validateVariantInput (input: paramsFormatType): void {
  const isInvalidInput = Object.keys(input).every(item => !VARIANT_QUERY_KEYS.includes(item as typeof VARIANT_QUERY_KEYS[number]))
  if (isInvalidInput) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one of these properties must be defined: spdi, hgvs, ca_id, variant_id'
    })
  }
}

function splitInput (input: paramsFormatType): { variantInput: paramsFormatType, edgeInput: paramsFormatType } {
  const variantInput: paramsFormatType = {}
  if (input.spdi !== undefined) variantInput.spdi = input.spdi
  if (input.hgvs !== undefined) variantInput.hgvs = input.hgvs
  if (input.ca_id !== undefined) variantInput.ca_id = input.ca_id
  if (input.variant_id !== undefined) variantInput.variant_id = input.variant_id

  const edgeInput: paramsFormatType = {}
  if (input.files_fileset !== undefined) edgeInput.files_fileset = input.files_fileset
  if (input.biosample_term !== undefined) edgeInput.biosample_term = input.biosample_term
  if (input.biological_context !== undefined) edgeInput.biological_context = input.biological_context

  return { variantInput, edgeInput }
}

function buildEdgeFilters (input: paramsFormatType): string {
  const filters: string[] = []

  if (input.files_fileset !== undefined) {
    filters.push(`record.files_filesets == 'files_filesets/${input.files_fileset as string}'`)
    delete input.files_fileset
  }
  if (input.biosample_term !== undefined) {
    filters.push(`record.biosample_term == 'ontology_terms/${input.biosample_term as string}'`)
    delete input.biosample_term
  }
  if (input.biological_context !== undefined) {
    const biologicalContext = (input.biological_context as string).replace(/"/g, '\\"')
    filters.push(`record.biological_context == "${biologicalContext}"`)
    delete input.biological_context
  }

  if (filters.length === 0) {
    return ''
  }
  return `FILTER ${filters.join(' AND ')}`
}

function buildMainQuery (nearbyGenes: boolean, edgeFilters: string): string {
  const geneFilters = nearbyGenes
    ? `
        FILTER targetGene.chr == @chr
        LET geneTss = targetGene.strand == '-' ? targetGene.end : targetGene.start
        LET distanceToTss = MIN([ABS(ge.start - geneTss), ABS(ge.end - geneTss)])
        FILTER distanceToTss <= ${DISTANCE_TO_TSS_BP}`
    : ''

  const distanceReturn = nearbyGenes ? 'distance_to_tss: distanceToTss,' : ''

  return `
    FOR ge IN @elements
      FOR record IN genomic_elements_genes
        FILTER record._from == ge._id
        FILTER record.method == 'Perturb-seq'
        ${edgeFilters}

        LET targetGene = DOCUMENT(record._to)
        FILTER targetGene != null
        ${geneFilters}
    SORT record.neg_log10_pvalue_adj DESC
    LIMIT @offset, @limit
    RETURN {
        variant: @variant,
        ${distanceReturn}
        genomic_element: {
          _id: ge._key,
          name: ge.name,
          chr: ge.chr,
          start: ge.start,
          end: ge.end,
          type: ge.type,
          source: ge.source,
          source_url: ge.source_url
        },
        gene: {
          _id: targetGene._key,
          name: targetGene.name,
          chr: targetGene.chr,
          start: targetGene.start,
          end: targetGene.end,
          strand: targetGene.strand
        },
        name: record.name,
        label: record.label,
        method: record.method,
        class: record.class,
        source: record.source,
        source_url: record.source_url,
        files_filesets: record.files_filesets,
        biological_context: record.biological_context,
        biosample_term: record.biosample_term,
        crispr_modality: record.crispr_modality,
        log2FC: record.log2FC,
        neg_log10_pvalue: record.neg_log10_pvalue,
        neg_log10_pvalue_adj: record.neg_log10_pvalue_adj,
        p_value: record.p_value,
        p_value_adj: record.p_value_adj,
        effect_size: record.effect_size,
        significant: record.significant
      }
  `
}

async function findGenesFromVariantViaElements (input: paramsFormatType): Promise<any[]> {
  validateVariantInput(input)

  const { variantInput, edgeInput } = splitInput(input)

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  const page = input.page as number
  delete input.page

  const nearbyGenes = input.nearby_genes !== 'false'
  delete input.nearby_genes

  const edgeFilters = buildEdgeFilters(edgeInput)

  const variants = await variantSearch({
    ...variantInput,
    organism: 'Homo sapiens',
    page: 0,
    limit: 1
  })
  if (variants.length === 0) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Variant not found.'
    })
  }
  const variant = variants[0]

  // Region + method in one AQL FILTER makes ArangoDB prefer the method-leading
  // index (~10s). Query region alone (force chr/start/end), then filter method
  // in application code (~0.4s, no length bound needed).
  const overlappingElementsQuery = `
    FOR ge IN genomic_elements
      OPTIONS { indexHint: "idx_persistent_chr_start_end", forceIndexHint: true }
      FILTER ge.chr == @chr AND ge.start <= @pos AND ge.end > @pos
      RETURN ge
  `
  const overlappingElementsBindVars = { chr: variant.chr, pos: variant.pos }

  const overlappingCandidates = await (await db.query(overlappingElementsQuery, overlappingElementsBindVars)).all()
  const overlappingElements = overlappingCandidates.filter(
    (ge: { method?: string }) => ge.method === OVERLAPPING_ELEMENT_METHOD
  )

  if (overlappingElements.length === 0) {
    return []
  }

  const query = buildMainQuery(nearbyGenes, edgeFilters)

  const mainBindVars: Record<string, unknown> = {
    elements: overlappingElements,
    variant: {
      _id: variant._id,
      chr: variant.chr,
      pos: variant.pos,
      ref: variant.ref,
      alt: variant.alt,
      rsid: variant.rsid,
      spdi: variant.spdi,
      hgvs: variant.hgvs,
      ca_id: variant.ca_id
    },
    offset: page * limit,
    limit
  }
  if (nearbyGenes) {
    mainBindVars.chr = variant.chr
  }

  return await (await db.query(query, mainBindVars)).all()
}

const variantsGenomicElementsGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/genomic-elements/genes', description: descriptions.variants_genomic_elements_genes, tags: ['Bespoke Endpoints'] } })
  .input(inputFormat)
  .output(outputFormat)
  .query(async ({ input }) => await findGenesFromVariantViaElements(input))

export const variantsGenomicElementsGenesRouters = {
  variantsGenomicElementsGenes
}
