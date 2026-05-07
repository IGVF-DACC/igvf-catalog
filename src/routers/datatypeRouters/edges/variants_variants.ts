import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import {
  variantSearch, singleVariantQueryFormat, variantFormat,
  variantSimplifiedFormat, variantIDSearch, parseRegion
} from '../nodes/variants'
import { descriptions } from '../descriptions'
import { type paramsFormatType } from '../_helpers'
import { TRPCError } from '@trpc/server'
import { commonHumanEdgeParamsFormat, variantsCommonQueryFormat } from '../params'
import { getCollectionEnumValuesOrThrow, getSchema } from '../schema'
import {
  chQuery, getChSelectStatements, getChTableSchema, loadJsonSchema,
  type QueryParams
} from '../clickhouse_helpers'

const MAX_PAGE_SIZE = 500

const MAX_SUMMARY_PAGE_SIZE = 100
const DEFAULT_SUMMARY_PAGE_SIZE = 15

const ldSchemaObj = getSchema('data/schemas/edges/variants_variants.TopLD.json')
const ldCollectionName = ldSchemaObj.db_collection_name as string
const variantsSchemaObj = getSchema('data/schemas/nodes/variants.Favor.json')
const variantCollectionName = variantsSchemaObj.db_collection_name as string

const ancestries = getCollectionEnumValuesOrThrow('edges', 'variants_variants', 'ancestry')

const tfBindingFormat = z.object({
  motif: z.string(),
  count: z.number(),
  cell_types: z.array(z.object({
    cell_type: z.string().nullable(),
    count: z.number()
  }))
})

const qtlsFormat = z.object({
  type: z.string(),
  cell_types: z.array(z.object({
    name: z.string().nullable(),
    count: z.number()
  })),
  genes: z.array(z.object({
    name: z.string(),
    count: z.number()
  }))
})

const variantsVariantsSummaryFormat = z.object({
  ancestry: z.string(),
  d_prime: z.number().nullish(),
  r2: z.number().nullish(),
  'sequence variant': z.string().or(variantSimplifiedFormat),
  predictions: z.object({
    qtls: z.array(qtlsFormat).nullish(),
    tf_binding: z.array(tfBindingFormat).nullish()
  })
})

const variantsVariantsFormat = z.object({
  chr: z.string().nullable(),
  ancestry: z.string().nullable(),
  d_prime: z.number().nullable(),
  r2: z.number().nullable(),
  label: z.string(),
  variant_1_base_pair: z.string(),
  variant_1_rsid: z.string(),
  variant_2_base_pair: z.string(),
  variant_2_rsid: z.string(),
  variant_1_pos: z.number().nullish(),
  variant_1_spdi: z.string().nullish(),
  variant_1_hgvs: z.string().nullish(),
  variant_2_pos: z.number().nullish(),
  variant_2_spdi: z.string().nullish(),
  variant_2_hgvs: z.string().nullish(),
  source: z.string().optional(),
  source_url: z.string().optional(),
  sequence_variant: z.string().or(z.array(variantFormat)).optional(),
  name: z.string()
})

const variantLDQueryFormat = z.object({
  r2: z.string().trim().optional(),
  d_prime: z.string().trim().optional(),
  ancestry: z.enum(ancestries).optional()
})

// ---------------------------------------------------------------------------
// ClickHouse SELECT constants for findVariantLDs (built once at import time)
// ---------------------------------------------------------------------------

const variantsChSchema = getChTableSchema('variants')
const favorJsonSchema = loadJsonSchema('nodes/variants.Favor.json')

// Full variant record for verbose mode (matches variantFormat / Favor schema).
const VARIANT_FULL_SELECT = getChSelectStatements(favorJsonSchema, variantsChSchema, 'v')

// Lean lookup for non-verbose: only pos/spdi/hgvs needed for variant_*_pos/spdi/hgvs fields.
const VARIANT_LOOKUP_SELECT = 'v.id AS _id, v.pos AS pos, v.spdi AS spdi, v.hgvs AS hgvs'

// ---------------------------------------------------------------------------
// Range-filter helpers for r2 / d_prime (Float32). Shape mirrors
// variants_phenotypes.ts's parseRangeFilter; can be extracted to a shared
// module in a follow-up port.
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

const RANGE_OP_MAP: Record<string, string> = { gt: '>', gte: '>=', lt: '<', lte: '<=', eq: '=' }

function rangeCondition (
  filter: { op: string, val: number, val2?: number },
  column: string,
  paramPrefix: string,
  params: QueryParams
): string {
  if (filter.op === 'range') {
    params[`${paramPrefix}_lo`] = filter.val
    params[`${paramPrefix}_hi`] = filter.val2!
    return `${column} >= {${paramPrefix}_lo:Float32} AND ${column} < {${paramPrefix}_hi:Float32}`
  }
  params[paramPrefix] = filter.val
  return `${column} ${RANGE_OP_MAP[filter.op] ?? '>='} {${paramPrefix}:Float32}`
}

// ---------------------------------------------------------------------------
// LD WHERE-builder
// ---------------------------------------------------------------------------

interface LDFilter {
  variantIds?: string[]
  variantsRegion?: { chr: string, start: number, end: number }
  ancestry?: string
  r2?: ReturnType<typeof parseRangeFilter>
  dPrime?: ReturnType<typeof parseRangeFilter>
}

function buildLDWhere (filter: LDFilter, params: QueryParams): string {
  const conds: string[] = []

  if (filter.variantsRegion !== undefined) {
    // Region pushed down as subquery — avoids materializing thousands of variant
    // IDs that would blow ClickHouse's max_query_size. Same pattern as
    // /variants/phenotypes?region=...
    conds.push(
      'variants_1_id IN (SELECT id FROM variants WHERE chr = {_chr:String} ' +
      'AND pos >= {_rstart:UInt32} AND pos < {_rend:UInt32})'
    )
    params._chr = filter.variantsRegion.chr
    params._rstart = filter.variantsRegion.start
    params._rend = filter.variantsRegion.end
  } else if (filter.variantIds !== undefined && filter.variantIds.length > 0) {
    conds.push('variants_1_id IN ({_v_ids:Array(String)})')
    params._v_ids = filter.variantIds
  }

  if (filter.ancestry !== undefined) {
    conds.push('ancestry = {_anc:String}')
    params._anc = filter.ancestry
  }

  if (filter.r2 !== undefined) {
    conds.push(rangeCondition(filter.r2, 'r2', '_r2', params))
  }
  if (filter.dPrime !== undefined) {
    conds.push(rangeCondition(filter.dPrime, 'd_prime', '_dp', params))
  }

  return conds.length > 0 ? conds.join(' AND ') : '1=1'
}

// ---------------------------------------------------------------------------
// Row → API output transformation
// ---------------------------------------------------------------------------

interface VariantLookup {
  pos: number | null
  spdi: string | null
  hgvs: string | null
}

function transformLDRow (
  row: any,
  simpleMap: Map<string, VariantLookup>,
  verboseMap: Map<string, any> | null,
  verbose: boolean
): any {
  const v1 = simpleMap.get(row.variants_1_id)
  const v2 = simpleMap.get(row.variants_2_id)

  const sequenceVariant = verbose
    ? (verboseMap?.has(row.variants_2_id) ? [verboseMap.get(row.variants_2_id)] : [])
    : `variants/${row.variants_2_id as string}`

  return {
    chr: row.chr || null,
    ancestry: row.ancestry || null,
    d_prime: row.d_prime ?? null,
    r2: row.r2 ?? null,
    label: row.label,
    variant_1_base_pair: row.variant_1_base_pair,
    variant_1_rsid: row.variant_1_rsid,
    variant_2_base_pair: row.variant_2_base_pair,
    variant_2_rsid: row.variant_2_rsid,
    variant_1_pos: v1?.pos ?? null,
    variant_1_spdi: v1?.spdi || null,
    variant_1_hgvs: v1?.hgvs || null,
    variant_2_pos: v2?.pos ?? null,
    variant_2_spdi: v2?.spdi || null,
    variant_2_hgvs: v2?.hgvs || null,
    source: row.source,
    source_url: row.source_url,
    sequence_variant: sequenceVariant,
    name: row.name
  }
}

export async function findVariantLDSummary (input: paramsFormatType): Promise<any[]> {
  const originalPage = input.page as number

  let limit = DEFAULT_SUMMARY_PAGE_SIZE
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_SUMMARY_PAGE_SIZE) ? input.limit as number : MAX_SUMMARY_PAGE_SIZE
    delete input.limit
  }

  if (input.spdi === undefined && input.hgvs === undefined && input.variant_id === undefined && input.ca_id === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one parameter must be defined.'
    })
  }

  input.page = 0
  const variant = (await variantSearch(input))

  if (variant.length === 0) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Variant not found.'
    })
  }

  const id = `variants/${variant[0]._id as string}`

  // temporarily removing genomic elements related queries until we have a better way to handle the performance
  const query = `
  FOR record IN ${ldCollectionName}
    FILTER (record._from == '${id}' OR record._to == '${id}')
    SORT record._key

    LET otherRecordKey = PARSE_IDENTIFIER(record._from == '${id}' ? record._to : record._from).key

    LET v = DOCUMENT('${variantCollectionName}', otherRecordKey)
    LET variant = {
      _id: v._key,
      chr: v.chr,
      pos: v.pos,
      rsid: v.rsid,
      ref: v.ref,
      alt: v.alt,
      spdi: v.spdi,
      hgvs: v.hgvs,
      ca_id: v.ca_id
    }

    LET qtls = (
      FOR qlt IN variants_genes
      FILTER qlt._from == v._id
      COLLECT type = qlt.label INTO group
      LET cell_types_qtl = (
        FOR g IN group
        COLLECT biological_context = g.qlt.biological_context WITH COUNT INTO count
        RETURN { name: biological_context, count }
      )
      LET genes_qtl = (
        FOR g IN group
        COLLECT gene = g.qlt._to  WITH COUNT INTO count
        LET geneName = DOCUMENT(gene).name
        RETURN DISTINCT { name: geneName, count }
      )
      RETURN { type, cell_types: cell_types_qtl, genes: genes_qtl }
    )

    LET tf_binding = (
      FOR vp IN variants_proteins
      FILTER vp._from == v._id and vp.source == 'ADASTRA allele-specific TF binding calls' and vp.motif_conc != 'No Hit'
      COLLECT motif = vp.motif INTO group
      LET count = LENGTH(group)
      LET cell_types_tf = (
      FOR g IN group
        COLLECT cell_type = g.vp.biological_context WITH COUNT INTO termCount
        RETURN { cell_type, count: termCount }
    )

      RETURN { motif, count, cell_types: cell_types_tf }
    )

    LIMIT ${originalPage * limit}, ${limit}
    RETURN {
      'ancestry': record.ancestry,
      'd_prime': record.d_prime,
      'r2': record.r2,
      'sequence variant': MERGE(variant, { predictions: { qtls, tf_binding } })
    }
  `

  let objs = await (await db.query(query)).all()

  const markDeletion = new Set()
  for (let i = 0; i < objs.length; i++) {
    const element = objs[i]
    if (element['sequence variant']) {
      element.predictions = element['sequence variant'].predictions
      delete element['sequence variant'].predictions
    } else {
      // we need to remove records which we have no variants
      markDeletion.add(i)
    }
  }
  objs = objs.filter((_, index) => !markDeletion.has(index))
  return objs
}

function validateInput (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['variant_id', 'spdi', 'hgvs', 'ca_id', 'rsid', 'region'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one variant property must be defined.'
    })
  }
}

async function findVariantLDs (input: paramsFormatType): Promise<any[]> {
  validateInput(input)
  delete input.organism

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number) <= MAX_PAGE_SIZE ? (input.limit as number) : MAX_PAGE_SIZE
  }
  const page = (input.page as number) ?? 0
  const verbose = input.verbose === 'true'

  const filter: LDFilter = {}

  // Variant identifier resolution. Region takes its own subquery path
  // (no ID materialization) — same shape as /variants/phenotypes?region=...
  if (input.region !== undefined) {
    const r = parseRegion(input.region as string)
    if (r.end - r.start > 10000) {
      throw new TRPCError({ code: 'BAD_REQUEST', message: 'Region span exceeds 10kb.' })
    }
    filter.variantsRegion = r
  } else {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const variantInput: paramsFormatType = (({ variant_id, spdi, hgvs, ca_id, rsid }) =>
      ({ variant_id, spdi, hgvs, ca_id, rsid }))(input)
    filter.variantIds = await variantIDSearch(variantInput)
    if (filter.variantIds.length === 0) return []
  }

  if (input.ancestry !== undefined) filter.ancestry = input.ancestry as string
  if (input.r2 !== undefined) filter.r2 = parseRangeFilter(input.r2 as string)
  if (input.d_prime !== undefined) filter.dPrime = parseRangeFilter(input.d_prime as string)

  const params: QueryParams = {}
  const where = buildLDWhere(filter, params)
  params._lim = limit
  params._off = page * limit

  // Step A — page query against variants_variants. ORDER BY matches the PK
  // exactly; pagination is a continued range scan with no extra sort cost.
  const ldRows = await chQuery<any>(`
    SELECT chr, ancestry, d_prime, r2, label, name, source, source_url,
           variants_1_id, variants_2_id,
           variants_1_rsid       AS variant_1_rsid,
           variants_2_rsid       AS variant_2_rsid,
           variants_1_base_pair  AS variant_1_base_pair,
           variants_2_base_pair  AS variant_2_base_pair
    FROM variants_variants
    WHERE ${where}
    ORDER BY variants_1_id, ancestry, variants_2_id
    LIMIT {_lim:UInt32} OFFSET {_off:UInt32}
  `, params)

  if (ldRows.length === 0) return []

  // Step B — variant detail enrichment. Collect both v1 and v2 IDs from the
  // page (bounded by 2*limit ≤ 1000) and look them up by primary key on the
  // variants table. Verbose mode pulls the full record; non-verbose fetches
  // just pos/spdi/hgvs.
  const idSet = new Set<string>()
  for (const r of ldRows) {
    idSet.add(r.variants_1_id)
    idSet.add(r.variants_2_id)
  }
  const ids = Array.from(idSet)

  const simpleMap = new Map<string, VariantLookup>()
  const verboseMap: Map<string, any> | null = verbose ? new Map() : null

  if (ids.length > 0) {
    const select = verbose ? VARIANT_FULL_SELECT : VARIANT_LOOKUP_SELECT
    const rows = await chQuery<any>(
      `SELECT ${select} FROM variants v WHERE v.id IN ({_var_ids:Array(String)})`,
      { _var_ids: ids }
    )
    for (const r of rows) {
      simpleMap.set(r._id, {
        pos: r.pos ?? null,
        spdi: r.spdi || null,
        hgvs: r.hgvs || null
      })
      if (verboseMap !== null) verboseMap.set(r._id, r)
    }
  }

  return ldRows.map(r => transformLDRow(r, simpleMap, verboseMap, verbose))
}

const variantsFromVariantID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/variant-ld', description: descriptions.variants_variants } })
  .input(variantsCommonQueryFormat.merge(variantLDQueryFormat).merge(commonHumanEdgeParamsFormat))
  .output(z.array(variantsVariantsFormat))
  .query(async ({ input }) => await findVariantLDs(input))

const variantsFromVariantIDSummary = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/variant-ld/summary', description: descriptions.variants_variants_summary } })
  .input(singleVariantQueryFormat.merge(z.object({ page: z.number().default(0), limit: z.number().optional() })))
  .output(z.array(variantsVariantsSummaryFormat))
  .query(async ({ input }) => await findVariantLDSummary(input))

export const variantsVariantsRouters = {
  variantsFromVariantIDSummary,
  variantsFromVariantID
}
