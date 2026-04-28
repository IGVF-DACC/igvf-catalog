import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { studyFormat } from '../nodes/studies'
import { type paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { QUERY_LIMIT } from '../../../constants'
import { TRPCError } from '@trpc/server'
import { variantIDSearch, variantSimplifiedFormat, parseRegion } from '../nodes/variants'
import { commonHumanEdgeParamsFormat, variantsCommonQueryFormat } from '../params'
import {
  chQuery, sqlInList, getChSelectStatements, getChFilterConditions,
  getChTableSchema, loadJsonSchema, type QueryParams
} from '../clickhouse_helpers'

const MAX_PAGE_SIZE = 100
const METHODS = ['cV2F', 'SGE', 'GWAS'] as const
const LABELS = ['protein variant effect', 'predicted variant effect on phenotype', 'GWAS'] as const
const CLASS = ['observed data', 'prediction'] as const
const SOURCES = ['IGVF', 'OpenTargets'] as const

// ---------------------------------------------------------------------------
// Schemas (loaded once at import time)
// ---------------------------------------------------------------------------

const vpChSchema = getChTableSchema('variants_phenotypes')
const vpsChSchema = getChTableSchema('variants_phenotypes_studies')
const variantsChSchema = getChTableSchema('variants')
const studiesChSchema = getChTableSchema('studies')

const cV2FSchema = loadJsonSchema('edges/variants_phenotypes.cV2F.json')
const gwasVpSchema = loadJsonSchema('edges/variants_phenotypes.GWAS.json')
const vpsGwasSchema = loadJsonSchema('edges/variants_phenotypes_studies.GWAS.json')
const favorSchema = loadJsonSchema('nodes/variants.Favor.json')
const studyGwasSchema = loadJsonSchema('nodes/studies.GWAS.json')

// ---------------------------------------------------------------------------
// Schema-driven SELECT constants (built once)
// ---------------------------------------------------------------------------

const IGVF_SELECT = getChSelectStatements(cV2FSchema, vpChSchema, 'vp', {
  extraSelect: [
    'vp.id AS vp_id',
    'vp.variants_id AS variants_id',
    'ot.name AS phenotype_term',
    'vp.ontology_terms_id AS phenotype_id'
  ]
})

const GWAS_VP_SELECT = getChSelectStatements(gwasVpSchema, vpChSchema, 'vp', {
  skipFields: ['equivalent_ontology_term']
})
const GWAS_VPS_SELECT = getChSelectStatements(vpsGwasSchema, vpsChSchema, 'vps', {
  skipFields: ['_from']
})
const GWAS_SELECT = [
  'vp.id AS vp_id',
  GWAS_VP_SELECT,
  GWAS_VPS_SELECT,
  'vps.studies_id AS studies_id',
  'vp.variants_id AS variants_id'
].join(', ')

const VARIANT_SIMPLIFIED_SELECT = getChSelectStatements(favorSchema, variantsChSchema, 'v', {
  simplified: true
})

const STUDY_SELECT = getChSelectStatements(studyGwasSchema, studiesChSchema, 's')

// ---------------------------------------------------------------------------
// Zod input/output formats
// ---------------------------------------------------------------------------

const variantsPhenotypesQueryFormat = z.object({
  phenotype_id: z.string().trim().optional(),
  log10pvalue: z.string().trim().optional(),
  method: z.enum(METHODS).optional(),
  label: z.enum(LABELS).optional(),
  class: z.enum(CLASS).optional()
})

const phenotypesVariantsInputFormat = z.object({
  phenotype_id: z.string().trim().optional(),
  phenotype_name: z.string().trim().optional(),
  log10pvalue: z.string().trim().optional(),
  method: z.enum(METHODS).optional(),
  label: z.enum(LABELS).optional(),
  class: z.enum(CLASS).optional(),
  files_fileset: z.string().optional(),
  source: z.enum(SOURCES).optional()
}).merge(commonHumanEdgeParamsFormat)

const gwasVariantPhenotypeFormat = z.object({
  rsid: z.array(z.string()).nullish(),
  phenotype_term: z.string().nullable(),
  study: z.string().or(studyFormat).optional(),
  log10pvalue: z.number().nullable(),
  p_val: z.number().nullable(),
  beta: z.number().nullable(),
  beta_ci_lower: z.number().nullable(),
  beta_ci_upper: z.number().nullable(),
  oddsr_ci_lower: z.number().nullable(),
  oddsr_ci_upper: z.number().nullable(),
  lead_chrom: z.string().nullable(),
  lead_pos: z.number().nullable(),
  lead_ref: z.string().nullable(),
  lead_alt: z.string().nullable(),
  direction: z.string().nullable(),
  source: z.string().default('OpenTargets'),
  source_url: z.string().nullish(),
  class: z.string().nullish(),
  method: z.string().nullish(),
  label: z.string().nullish(),
  version: z.string().default('October 2022 (22.10)'),
  name: z.string(),
  variant: z.string().or(variantSimplifiedFormat)
})

const igvfVariantPhenotypeFormat = z.object({
  name: z.string(),
  source: z.string(),
  source_url: z.string(),
  score: z.number().nullable(),
  method: z.string().nullable(),
  class: z.string().nullish(),
  phenotype_term: z.string().nullable(),
  phenotype_id: z.string().nullish(),
  files_filesets: z.string().nullish(),
  biosample_term: z.string().nullish(),
  biological_context: z.string().nullish(),
  variant: z.string().or(variantSimplifiedFormat)
})

const variantPhenotypeFormat = gwasVariantPhenotypeFormat.or(igvfVariantPhenotypeFormat)

// ---------------------------------------------------------------------------
// P-value range helpers (VP-specific, not generic enough for the shared module)
// ---------------------------------------------------------------------------

function parseRangeFilter (value: string): { op: string, val: number, val2?: number } {
  if (value.startsWith('range:')) {
    const [lo, hi] = value.slice(6).split('-').map(Number)
    return { op: 'range', val: lo, val2: hi }
  }
  if (value.includes(':')) {
    const [op, num] = value.split(':')
    return { op, val: Number(num) }
  }
  return { op: 'gte', val: Number(value) }
}

function pvalueCondition (filter: { op: string, val: number, val2?: number }, params: QueryParams): string {
  const opMap: Record<string, string> = { gt: '>', gte: '>=', lt: '<', lte: '<=', eq: '=' }
  if (filter.op === 'range') {
    params._pval_lo = filter.val
    params._pval_hi = filter.val2!
    return 'vps.log10pvalue >= {_pval_lo:Float64} AND vps.log10pvalue < {_pval_hi:Float64}'
  }
  params._pval = filter.val
  return `vps.log10pvalue ${opMap[filter.op] ?? '>='} {_pval:Float64}`
}

// ---------------------------------------------------------------------------
// Condition builder for the variants_phenotypes table
// ---------------------------------------------------------------------------

interface VpFilter {
  phenotypeIds?: string[]
  variantIds?: string[]
  // For region inputs: a 1kb region can yield thousands of variant IDs, which
  // would blow ClickHouse's max_query_size when serialized as an IN list.
  // Push the region down as a subquery on the variants table instead.
  variantsRegion?: { chr: string, start: number, end: number }
  method?: string
  cls?: string
  label?: string
  fileset?: string
}

function buildVpWhere (filter: VpFilter, params: QueryParams): string {
  const conds: string[] = []

  if (filter.phenotypeIds !== undefined) {
    if (filter.phenotypeIds.length === 1) {
      conds.push('vp.ontology_terms_id = {_phenoId:String}')
      params._phenoId = filter.phenotypeIds[0]
    } else if (filter.phenotypeIds.length > 1) {
      conds.push(`vp.ontology_terms_id IN (${sqlInList(filter.phenotypeIds)})`)
    }
  }

  if (filter.variantsRegion !== undefined) {
    // Region pushed down as subquery — variants table is sorted by id (which
    // starts with the chromosome RefSeq accession), so chr/pos filters are
    // granule-pruned. Avoids materializing thousands of IDs in TS/SQL.
    conds.push('vp.variants_id IN (SELECT id FROM variants WHERE chr = {_vp_chr:String} AND pos >= {_vp_pos_start:Float64} AND pos < {_vp_pos_end:Float64})')
    params._vp_chr = filter.variantsRegion.chr
    params._vp_pos_start = filter.variantsRegion.start
    params._vp_pos_end = filter.variantsRegion.end
  } else if (filter.variantIds !== undefined && filter.variantIds.length > 0) {
    conds.push(`vp.variants_id IN (${sqlInList(filter.variantIds)})`)
  }

  // Schema-driven column filters (method, class, label)
  const genericFilters: Record<string, string | undefined> = {}
  if (filter.method !== undefined) genericFilters.method = filter.method
  if (filter.cls !== undefined) genericFilters.class = filter.cls
  if (filter.label !== undefined) genericFilters.label = filter.label

  const schemaConds = getChFilterConditions(cV2FSchema, vpChSchema, genericFilters, 'vp', params)
  conds.push(...schemaConds)

  // files_fileset has name mismatch + prefix transform — explicit handling
  if (filter.fileset !== undefined) {
    conds.push('vp.files_filesets = {_vpFileset:String}')
    params._vpFileset = `files_filesets/${filter.fileset}`
  }

  return conds.length > 0 ? conds.join(' AND ') : '1=1'
}

// ---------------------------------------------------------------------------
// Detail query builders (schema-driven column lists)
// ---------------------------------------------------------------------------

async function fetchVariantDetails (variantIds: string[]): Promise<Map<string, any>> {
  if (variantIds.length === 0) return new Map()
  const rows = await chQuery<any>(
    `SELECT ${VARIANT_SIMPLIFIED_SELECT} FROM variants v WHERE v.id IN (${sqlInList(variantIds)})`
  )
  const map = new Map<string, any>()
  for (const r of rows) map.set(r._id, r)
  return map
}

async function fetchStudyDetails (studyIds: string[]): Promise<Map<string, any>> {
  if (studyIds.length === 0) return new Map()
  const rows = await chQuery<any>(
    `SELECT ${STUDY_SELECT} FROM studies s WHERE s.id IN (${sqlInList(studyIds)})`
  )
  const map = new Map<string, any>()
  for (const r of rows) map.set(r._id, r)
  return map
}

async function queryIgvfRows (where: string, params: QueryParams, limit: number, offset: number): Promise<any[]> {
  const sql = `
    SELECT ${IGVF_SELECT}
    FROM variants_phenotypes vp
    JOIN ontology_terms ot ON ot.id = vp.ontology_terms_id
    WHERE vp.source = 'IGVF' AND ${where}
    ORDER BY vp.id
    LIMIT {_lim:UInt32} OFFSET {_off:UInt32}`

  return await chQuery(sql, { ...params, _lim: limit, _off: offset })
}

async function queryIgvfByIds (ids: string[]): Promise<any[]> {
  if (ids.length === 0) return []
  const sql = `
    SELECT ${IGVF_SELECT}
    FROM variants_phenotypes vp
    JOIN ontology_terms ot ON ot.id = vp.ontology_terms_id
    WHERE vp.id IN (${sqlInList(ids)})`

  return await chQuery(sql)
}

async function queryGwasRows (
  where: string, params: QueryParams,
  limit: number, offset: number,
  pvalFilter?: { op: string, val: number, val2?: number }
): Promise<any[]> {
  const pvalCond = pvalFilter !== undefined ? ` AND ${pvalueCondition(pvalFilter, params)}` : ''

  const sql = `
    SELECT ${GWAS_SELECT}
    FROM variants_phenotypes vp
    JOIN variants_phenotypes_studies vps ON vps.variants_phenotypes_id = vp.id
    WHERE ${where}${pvalCond}
    ORDER BY vps.id
    LIMIT {_lim:UInt32} OFFSET {_off:UInt32}`

  return await chQuery(sql, { ...params, _lim: limit, _off: offset })
}

async function queryGwasByVpIds (
  vpIds: string[],
  pvalFilter?: { op: string, val: number, val2?: number }
): Promise<any[]> {
  if (vpIds.length === 0) return []
  const params: QueryParams = {}
  const pvalCond = pvalFilter !== undefined ? ` AND ${pvalueCondition(pvalFilter, params)}` : ''

  const sql = `
    SELECT ${GWAS_SELECT}
    FROM variants_phenotypes vp
    JOIN variants_phenotypes_studies vps ON vps.variants_phenotypes_id = vp.id
    WHERE vp.id IN (${sqlInList(vpIds)})${pvalCond}
    LIMIT 1 BY vp.id`

  return await chQuery(sql, params)
}

// ---------------------------------------------------------------------------
// Row transformers
// ---------------------------------------------------------------------------

function variantField (row: any, variantMap: Map<string, any> | null): any {
  if (variantMap !== null) {
    const v = variantMap.get(row.variants_id)
    if (v !== undefined) {
      return {
        _id: v._id,
        chr: v.chr,
        pos: v.pos,
        alt: v.alt,
        ref: v.ref,
        rsid: v.rsid,
        spdi: v.spdi,
        hgvs: v.hgvs,
        ca_id: v.ca_id
      }
    }
  }
  return `variants/${row.variants_id}`
}

function studyFieldFromMap (row: any, studyMap: Map<string, any> | null): any {
  if (studyMap !== null) {
    const s = studyMap.get(row.studies_id)
    if (s !== undefined) {
      return {
        _id: s._id,
        name: s.name ?? null,
        source: s.source ?? null,
        source_url: s.source_url ?? null,
        ancestry_initial: s.ancestry_initial ?? null,
        ancestry_replication: s.ancestry_replication ?? null,
        n_cases: s.n_cases ?? null,
        n_initial: s.n_initial ?? null,
        n_replication: s.n_replication ?? null,
        pmid: s.pmid ?? null,
        pub_author: s.pub_author ?? null,
        pub_date: s.pub_date ?? null,
        pub_journal: s.pub_journal ?? null,
        pub_title: s.pub_title ?? null,
        has_sumstats: s.has_sumstats ?? null,
        num_assoc_loci: s.num_assoc_loci ?? null,
        study_source: s.study_source ?? null,
        trait_reported: s.trait_reported ?? null,
        trait_efos: s.trait_efos ?? null,
        trait_category: s.trait_category ?? null,
        version: s.version ?? null,
        study_type: s.study_type ?? null
      }
    }
  }
  return `studies/${row.studies_id}`
}

function toIgvfResult (row: any, variantMap: Map<string, any> | null): any {
  return {
    name: row.name,
    source: row.source,
    source_url: row.source_url,
    score: row.score ?? null,
    method: row.method ?? null,
    class: row.class ?? null,
    phenotype_term: row.phenotype_term ?? null,
    phenotype_id: row.phenotype_id ?? null,
    files_filesets: row.files_filesets ?? null,
    biosample_term: row.biosample_term ?? null,
    biological_context: row.biological_context ?? null,
    variant: variantField(row, variantMap)
  }
}

function toGwasResult (
  row: any,
  variantMap: Map<string, any> | null,
  studyMap: Map<string, any> | null,
  includeRsid: boolean = false
): any {
  const result: any = {
    phenotype_term: row.phenotype_term ?? null,
    study: studyFieldFromMap(row, studyMap),
    log10pvalue: row.log10pvalue ?? null,
    p_val: row.p_val ?? null,
    beta: row.beta ?? null,
    beta_ci_lower: row.beta_ci_lower ?? null,
    beta_ci_upper: row.beta_ci_upper ?? null,
    oddsr_ci_lower: row.oddsr_ci_lower ?? null,
    oddsr_ci_upper: row.oddsr_ci_upper ?? null,
    lead_chrom: row.lead_chrom ?? null,
    lead_pos: row.lead_pos ?? null,
    lead_ref: row.lead_ref ?? null,
    lead_alt: row.lead_alt ?? null,
    direction: row.direction ?? null,
    source: row.source ?? 'OpenTargets',
    class: row.class ?? null,
    method: row.method ?? null,
    label: row.label ?? null,
    version: row.version ?? 'October 2022 (22.10)',
    name: row.name,
    variant: variantField(row, variantMap)
  }
  if (includeRsid) {
    const v = variantMap?.get(row.variants_id)
    result.rsid = v?.rsid ?? null
  }
  return result
}

async function enrichIgvfRows (rows: any[], verbose: boolean): Promise<any[]> {
  const variantMap = verbose
    ? await fetchVariantDetails(Array.from(new Set(rows.map(r => r.variants_id))))
    : null
  return rows.map(r => toIgvfResult(r, variantMap))
}

async function enrichGwasRows (rows: any[], verbose: boolean, includeRsid: boolean = false): Promise<any[]> {
  const needVariants = verbose || includeRsid
  const [variantMap, studyMap] = await Promise.all([
    needVariants ? fetchVariantDetails(Array.from(new Set(rows.map(r => r.variants_id)))) : null,
    verbose ? fetchStudyDetails(Array.from(new Set(rows.map(r => r.studies_id)))) : null
  ])
  return rows.map(r => toGwasResult(r, variantMap, studyMap, includeRsid))
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

export function variantQueryValidation (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item =>
    !['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id', 'region', 'log10pvalue', 'files_fileset', 'method'].includes(item)
  )
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one variant property or log10pvalue or files_filesets must be defined.'
    })
  }
}

// ---------------------------------------------------------------------------
// Input parsing helpers
// ---------------------------------------------------------------------------

function extractPagination (input: paramsFormatType): { limit: number, offset: number } {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = Math.min(input.limit as number, MAX_PAGE_SIZE)
  }
  const page = (input.page as number) ?? 0
  return { limit, offset: page * limit }
}

function extractVpFilter (input: paramsFormatType): VpFilter {
  const filter: VpFilter = {}
  if (input.method !== undefined) filter.method = input.method as string
  if (input.class !== undefined) filter.cls = input.class as string
  if (input.label !== undefined) filter.label = input.label as string
  if (input.files_fileset !== undefined) filter.fileset = input.files_fileset as string
  return filter
}

// ---------------------------------------------------------------------------
// Query: GET /phenotypes/variants
// ---------------------------------------------------------------------------

async function findVariantsFromPhenotypesSearch (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  const { limit, offset } = extractPagination(input)
  const verbose = input.verbose === 'true'
  const sourceFilter = input.source as string | undefined
  const vpFilter = extractVpFilter(input)

  let pvalFilter: { op: string, val: number, val2?: number } | undefined
  if (input.log10pvalue !== undefined) {
    pvalFilter = parseRangeFilter(input.log10pvalue as string)
  }

  if (input.phenotype_id !== undefined) {
    vpFilter.phenotypeIds = [input.phenotype_id as string]
  } else if (input.phenotype_name !== undefined) {
    const terms = await chQuery<{ id: string }>(
      'SELECT id FROM ontology_terms WHERE name = {pName:String}',
      { pName: input.phenotype_name as string }
    )
    if (terms.length === 0) return []
    vpFilter.phenotypeIds = terms.map(t => t.id)
  } else {
    if (vpFilter.method === undefined && vpFilter.fileset === undefined && vpFilter.label === undefined) {
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: 'Either phenotype id, phenotype, method, or files_fileset must be defined.'
      })
    }
    const params: QueryParams = {}
    const where = buildVpWhere(vpFilter, params)
    const rows = await queryIgvfRows(where, params, limit, offset)
    return await enrichIgvfRows(rows, verbose)
  }

  const params: QueryParams = {}
  const where = buildVpWhere(vpFilter, params)

  if (sourceFilter === 'IGVF') {
    const rows = await queryIgvfRows(where, params, limit, offset)
    return await enrichIgvfRows(rows, verbose)
  }

  if (sourceFilter === 'OpenTargets') {
    const rows = await queryGwasRows(where, params, limit, offset, pvalFilter)
    return await enrichGwasRows(rows, verbose)
  }

  const vpPage = await chQuery<{ id: string, source: string }>(
    `SELECT vp.id AS id, vp.source AS source FROM variants_phenotypes vp WHERE ${where} ORDER BY vp.id LIMIT {_lim:UInt32} OFFSET {_off:UInt32}`,
    { ...params, _lim: limit, _off: offset }
  )
  if (vpPage.length === 0) return []

  const igvfIds = vpPage.filter(r => r.source === 'IGVF').map(r => r.id)
  const gwasIds = vpPage.filter(r => r.source !== 'IGVF').map(r => r.id)

  const [igvfRows, gwasRows] = await Promise.all([
    queryIgvfByIds(igvfIds),
    queryGwasByVpIds(gwasIds, pvalFilter)
  ])

  const allRows = [...igvfRows, ...gwasRows]
  const variantMap = verbose
    ? await fetchVariantDetails(Array.from(new Set(allRows.map(r => r.variants_id))))
    : null
  const studyMap = verbose
    ? await fetchStudyDetails(Array.from(new Set(gwasRows.map(r => r.studies_id))))
    : null

  const resultMap = new Map<string, any>()
  for (const r of igvfRows) resultMap.set(r.vp_id, toIgvfResult(r, variantMap))
  for (const r of gwasRows) resultMap.set(r.vp_id, toGwasResult(r, variantMap, studyMap))
  return vpPage.map(p => resultMap.get(p.id)).filter(Boolean)
}

// ---------------------------------------------------------------------------
// Query: GET /variants/phenotypes
// ---------------------------------------------------------------------------

async function findPhenotypesFromVariantSearch (input: paramsFormatType): Promise<any[]> {
  const { limit, offset } = extractPagination(input)
  variantQueryValidation(input)
  delete input.organism
  const verbose = input.verbose === 'true'
  const vpFilter = extractVpFilter(input)

  let pvalFilter: { op: string, val: number, val2?: number } | undefined
  if (input.log10pvalue !== undefined) {
    pvalFilter = parseRangeFilter(input.log10pvalue as string)
    delete input.log10pvalue
  }

  const hasVariantQuery = Object.keys(input).some(item =>
    ['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id', 'region'].includes(item)
  )
  if (hasVariantQuery) {
    if (input.region !== undefined) {
      // Region path: push a subquery into vp instead of materializing IDs.
      // Enforce the 10kb cap (was previously enforced inside variantIDSearch).
      const r = parseRegion(input.region as string)
      if (r.end - r.start > 10000) {
        throw new TRPCError({ code: 'BAD_REQUEST', message: 'Region span exceeds 10kb.' })
      }
      vpFilter.variantsRegion = r
    } else {
      // eslint-disable-next-line @typescript-eslint/naming-convention
      const variantInput: paramsFormatType = (({ variant_id, spdi, hgvs, ca_id, rsid }) =>
        ({ variant_id, spdi, hgvs, ca_id, rsid }))(input)
      vpFilter.variantIds = await variantIDSearch(variantInput)
    }
  }

  if (input.phenotype_id !== undefined) {
    vpFilter.phenotypeIds = [input.phenotype_id as string]
  }

  const igvfOnly = vpFilter.fileset !== undefined
  const params: QueryParams = {}
  const where = buildVpWhere(vpFilter, params)

  if (igvfOnly) {
    const rows = await queryIgvfRows(where, params, limit, offset)
    return await enrichIgvfRows(rows, verbose)
  }

  const vpPage = await chQuery<{ id: string, source: string }>(
    `SELECT vp.id AS id, vp.source AS source FROM variants_phenotypes vp WHERE ${where} ORDER BY vp.id LIMIT {_lim:UInt32} OFFSET {_off:UInt32}`,
    { ...params, _lim: limit, _off: offset }
  )
  if (vpPage.length === 0) return []

  const igvfIds = vpPage.filter(r => r.source === 'IGVF').map(r => r.id)
  const gwasIds = vpPage.filter(r => r.source !== 'IGVF').map(r => r.id)

  const [igvfRows, gwasRows] = await Promise.all([
    queryIgvfByIds(igvfIds),
    queryGwasByVpIds(gwasIds, pvalFilter)
  ])

  const allRows = [...igvfRows, ...gwasRows]
  const [variantMap, studyMap] = await Promise.all([
    verbose ? fetchVariantDetails(Array.from(new Set(allRows.map(r => r.variants_id)))) : null,
    verbose ? fetchStudyDetails(Array.from(new Set(gwasRows.map(r => r.studies_id)))) : null
  ])

  const resultMap = new Map<string, any>()
  for (const r of igvfRows) resultMap.set(r.vp_id, toIgvfResult(r, variantMap))
  for (const r of gwasRows) resultMap.set(r.vp_id, toGwasResult(r, variantMap, studyMap, true))
  return vpPage.map(p => resultMap.get(p.id)).filter(Boolean)
}

// ---------------------------------------------------------------------------
// tRPC route definitions
// ---------------------------------------------------------------------------

const variantsFromPhenotypes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/phenotypes/variants', description: descriptions.phenotypes_variants } })
  .input(phenotypesVariantsInputFormat)
  .output(z.array(variantPhenotypeFormat))
  .query(async ({ input }) => await findVariantsFromPhenotypesSearch(input))

const phenotypesFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/phenotypes', description: descriptions.variants_phenotypes } })
  .input(variantsCommonQueryFormat.merge(variantsPhenotypesQueryFormat).merge(commonHumanEdgeParamsFormat).merge(z.object({ files_fileset: z.string().optional() })))
  .output(z.array(variantPhenotypeFormat))
  .query(async ({ input }) => await findPhenotypesFromVariantSearch(input))

export const variantsPhenotypesRouters = {
  variantsFromPhenotypes,
  phenotypesFromVariants
}
