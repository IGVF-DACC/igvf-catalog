import { z } from 'zod'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { type paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonNodesParamsFormat } from '../params'
import { getCollectionEnumValuesOrThrow } from '../schema'
import {
  chQuery, getChSelectStatements, getChTableSchema, loadJsonSchema,
  type QueryParams
} from '../clickhouse_helpers'
import { parseRegion } from './variants'

const MAX_PAGE_SIZE = 500

const genesJsonSchema = loadJsonSchema('nodes/genes.GencodeGene.json')
const genesChSchema = getChTableSchema('genes')

// `gene_id` and `organism` aren't in the public API output schema (geneFormat
// has additionalProperties: false), so skip them from SELECT.
const GENE_SELECT = getChSelectStatements(genesJsonSchema, genesChSchema, 'g', {
  skipFields: ['gene_id', 'organism']
})

// Subset that overlaps with proj_by_chr_start so nearestGeneSearch can be
// answered entirely from the projection. Hand-written rather than schema-driven
// because the projection's column list is its own contract.
const GENE_SELECT_NEAREST = [
  'g.id AS _id', 'g.chr AS chr', 'g.start AS start', 'g.end AS end',
  'g.gene_type AS gene_type', 'g.name AS name', 'g.strand AS strand'
].join(', ')

const GENE_TYPES = getCollectionEnumValuesOrThrow('nodes', 'genes', 'gene_type')
const GENE_COLLECTIONS = getCollectionEnumValuesOrThrow('nodes', 'genes', 'collections')
const GENE_STUDY_SETS = getCollectionEnumValuesOrThrow('nodes', 'genes', 'study_sets')

export const genesQueryFormat = z.object({
  gene_id: z.string().trim().optional(),
  hgnc_id: z.string().trim().optional(),
  entrez: z.string().trim().optional(),
  name: z.string().trim().optional(),
  region: z.string().trim().optional(),
  synonym: z.string().trim().optional(),
  collection: z.enum(GENE_COLLECTIONS).optional(),
  study_set: z.enum(GENE_STUDY_SETS).optional(),
  gene_type: z.enum(GENE_TYPES).optional()
}).merge(commonNodesParamsFormat)

export const geneFormat = z.object({
  _id: z.string(),
  chr: z.string(),
  start: z.number().nullable(),
  end: z.number().nullable(),
  gene_type: z.string().nullable(),
  name: z.string(),
  strand: z.string().optional().nullable(),
  hgnc: z.string().optional().nullable(),
  entrez: z.string().optional().nullable(),
  collections: z.array(z.string()).optional().nullable(),
  study_sets: z.array(z.string()).optional().nullable(),
  source: z.string(),
  version: z.string(),
  source_url: z.string(),
  synonyms: z.array(z.string()).optional().nullable()
})

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function emptyToNull<T> (v: T | string | T[]): T | null {
  if (typeof v === 'string') return v === '' ? null : (v as T)
  if (Array.isArray(v)) return v.length === 0 ? null : (v as T)
  return v ?? null
}

function transformGeneRow (row: any): any {
  return {
    _id: row._id,
    chr: row.chr,
    start: row.start,
    end: row.end,
    gene_type: emptyToNull(row.gene_type),
    name: row.name,
    strand: emptyToNull(row.strand),
    hgnc: emptyToNull(row.hgnc),
    entrez: emptyToNull(row.entrez),
    collections: emptyToNull(row.collections),
    study_sets: emptyToNull(row.study_sets),
    source: row.source,
    version: row.version,
    source_url: row.source_url,
    synonyms: emptyToNull(row.synonyms)
  }
}

// Score expression — used only when `name` is provided. See
// clickhouserewrite/routers/genes.md for the structural walkthrough.
const SCORE_EXPR = `
  multiIf(
    name_lower = {_q:String}, 0,
    symbol_lower = {_q:String}, 0,
    has(synonyms_lower, {_q:String}), 1,
    least(
      editDistanceUTF8(name_lower, {_q:String}),
      editDistanceUTF8(symbol_lower, {_q:String}),
      arrayMin(arrayConcat(
        [toUInt64(4294967295)],
        arrayMap(
          s -> toUInt64(editDistanceUTF8(s, {_q:String})),
          arrayFilter(
            s -> abs(toInt32(length(s)) - toInt32(length({_q:String}))) <= 2,
            synonyms_lower
          )
        )
      ))
    ) + 2
  ) AS _score
`

// WHERE fragment for the unified-search OR group. Pulled inline once `_q` is
// already in `params`. The length prefilters skip editDistance evaluation for
// rows that can't possibly match (string-length difference > 2 implies edit
// distance > 2).
const NAME_SEARCH_OR = `
  (
    name_lower = {_q:String}
    OR symbol_lower = {_q:String}
    OR has(synonyms_lower, {_q:String})
    OR (
      abs(toInt32(length(name_lower)) - toInt32(length({_q:String}))) <= 2
      AND editDistanceUTF8(name_lower, {_q:String}) <= 2
    )
    OR (
      abs(toInt32(length(symbol_lower)) - toInt32(length({_q:String}))) <= 2
      AND editDistanceUTF8(symbol_lower, {_q:String}) <= 2
    )
    OR arrayExists(
      s -> abs(toInt32(length(s)) - toInt32(length({_q:String}))) <= 2
           AND editDistanceUTF8(s, {_q:String}) <= 2,
      synonyms_lower
    )
  )
`

function buildGenesWhere (input: paramsFormatType, params: QueryParams): string {
  const conds: string[] = []

  // Organism filter is always applied. Default per OpenAPI: Homo sapiens.
  conds.push('organism = {_org:String}')
  params._org = (input.organism as string | undefined) ?? 'Homo sapiens'

  if (input.gene_id !== undefined) {
    // Accept both unversioned (PK hit) and versioned (`idx_gene_id`) forms.
    conds.push('(id = {_gid:String} OR gene_id = {_gid:String})')
    params._gid = input.gene_id as string
  }

  if (input.hgnc_id !== undefined) {
    let hgnc = input.hgnc_id as string
    if (!hgnc.startsWith('HGNC:')) hgnc = `HGNC:${hgnc}`
    conds.push('hgnc = {_hgnc:String}')
    params._hgnc = hgnc
  }

  if (input.entrez !== undefined) {
    let entrez = input.entrez as string
    if (!entrez.startsWith('ENTREZ:')) entrez = `ENTREZ:${entrez}`
    conds.push('entrez = {_entrez:String}')
    params._entrez = entrez
  }

  if (typeof input.name === 'string' && input.name.length > 0) {
    // _q is set by the caller before buildGenesWhere is invoked.
    conds.push(NAME_SEARCH_OR)
  }

  if (input.synonym !== undefined) {
    conds.push('has(synonyms_lower, {_syn:String})')
    params._syn = (input.synonym as string).toLowerCase()
  }

  if (input.region !== undefined) {
    const r = parseRegion(input.region as string)
    conds.push('chr = {_chr:String} AND end > {_rstart:UInt32} AND start < {_rend:UInt32}')
    params._chr = r.chr
    params._rstart = r.start
    params._rend = r.end
  }

  if (input.gene_type !== undefined) {
    conds.push('gene_type = {_gtype:String}')
    params._gtype = input.gene_type as string
  }

  if (input.collection !== undefined) {
    conds.push('has(collections, {_coll:String})')
    params._coll = input.collection as string
  }

  if (input.study_set !== undefined) {
    conds.push('has(study_sets, {_ss:String})')
    params._ss = input.study_set as string
  }

  return conds.join(' AND ')
}

// ---------------------------------------------------------------------------
// Query: GET /genes
// ---------------------------------------------------------------------------

export async function geneSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number) <= MAX_PAGE_SIZE ? (input.limit as number) : MAX_PAGE_SIZE
  }
  const page = (input.page as number) ?? 0

  const params: QueryParams = {}

  const hasName = typeof input.name === 'string' && (input.name as string).length > 0
  if (hasName) params._q = (input.name as string).toLowerCase()

  const where = buildGenesWhere(input, params)
  const select = hasName ? `${GENE_SELECT}, ${SCORE_EXPR}` : GENE_SELECT
  const orderBy = hasName ? '_score, id' : 'id'

  params._lim = limit
  params._off = page * limit

  const sql = `
    SELECT ${select}
    FROM genes g
    WHERE ${where}
    ORDER BY ${orderBy}
    LIMIT {_lim:UInt32} OFFSET {_off:UInt32}
  `

  const rows = await chQuery<any>(sql, params)
  return rows.map(transformGeneRow)
}

// ---------------------------------------------------------------------------
// Query: nearest gene helper used by /variants/summary
// ---------------------------------------------------------------------------

export async function nearestGeneSearch (input: paramsFormatType): Promise<any[]> {
  if (input.region === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Region format invalid. Please use the format as the example: "chr1:12345-54321"'
    })
  }
  const { chr, start, end } = parseRegion(input.region as string)

  const baseParams: QueryParams = { _chr: chr }
  let typeFilter = ''
  if (input.gene_type !== undefined) {
    typeFilter = ' AND gene_type = {_gtype:String}'
    baseParams._gtype = input.gene_type as string
  }

  // Phase 1: any gene whose body overlaps the input region.
  const inRegion = await chQuery<any>(
    `SELECT ${GENE_SELECT_NEAREST} FROM genes g
       WHERE g.chr = {_chr:String} AND g.end > {_rstart:UInt32} AND g.start < {_rend:UInt32}${typeFilter}`,
    { ...baseParams, _rstart: start, _rend: end }
  )
  if (inRegion.length > 0) return inRegion.map(transformGeneRow)

  // Phase 2: nearest left + right via the (chr, start) projection. LIMIT 1 each.
  const [left, right] = await Promise.all([
    chQuery<any>(
      `SELECT ${GENE_SELECT_NEAREST} FROM genes g
         WHERE g.chr = {_chr:String} AND g.end < {_rstart:UInt32}${typeFilter}
         ORDER BY g.end DESC LIMIT 1`,
      { ...baseParams, _rstart: start }
    ),
    chQuery<any>(
      `SELECT ${GENE_SELECT_NEAREST} FROM genes g
         WHERE g.chr = {_chr:String} AND g.start > {_rend:UInt32}${typeFilter}
         ORDER BY g.start ASC LIMIT 1`,
      { ...baseParams, _rend: end }
    )
  ])
  return [...left, ...right].map(transformGeneRow)
}

const genes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes', description: descriptions.genes } })
  .input(genesQueryFormat)
  .output(z.array(geneFormat))
  .query(async ({ input }) => await geneSearch(input))

export const genesRouters = {
  genes
}
