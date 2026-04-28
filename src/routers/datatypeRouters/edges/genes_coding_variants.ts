import { z } from 'zod'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { type paramsFormatType } from '../_helpers'
import { publicProcedure } from '../../../trpc'
import { commonHumanEdgeParamsFormat, genesCommonQueryFormat } from '../params'
import { variantSimplifiedFormat } from '../nodes/variants'
import { getCollectionEnumValuesOrThrow } from '../schema'
import {
  chQuery, sqlInList, getChSelectStatements, getChTableSchema, loadJsonSchema,
  type QueryParams
} from '../clickhouse_helpers'

const QUERY_LIMIT = 500

const DATASETS = getCollectionEnumValuesOrThrow('edges', 'coding_variants_phenotypes', 'method')

// ---------------------------------------------------------------------------
// ClickHouse schema / SELECT constants (built once at import time)
// ---------------------------------------------------------------------------

const variantsChSchema = getChTableSchema('variants')
const favorSchema = loadJsonSchema('nodes/variants.Favor.json')
const VARIANT_SIMPLIFIED_SELECT = getChSelectStatements(favorSchema, variantsChSchema, 'v', { simplified: true })

// Static map: dataset enum value → score column name.
// Column name comes from this map, never from raw user input, so interpolation is safe.
const DATASET_SCORE_COL: Readonly<Record<string, string>> = {
  'VAMP-seq': 'score',
  SGE: 'score',
  'ESM-1v': 'esm_1v_score',
  MutPred2: 'pathogenicity_score'
}


// ---------------------------------------------------------------------------
// Zod input / output formats
// ---------------------------------------------------------------------------

const geneQueryFormat = genesCommonQueryFormat.merge(z.object({
  method: z.enum(DATASETS).optional(),
  files_fileset: z.string().optional()
})).merge(commonHumanEdgeParamsFormat).omit({ organism: true, verbose: true })

const allVariantsQueryFormat = z.object({
  gene_id: z.string(),
  dataset: z.enum(DATASETS),
  page: z.number().default(0),
  limit: z.number().optional()
})

const codingVariantsScoresFormat = z.object({
  protein_change: z.object({
    coding_variant_id: z.string().nullish(),
    protein_id: z.string().nullish(),
    protein_name: z.string().nullish(),
    transcript_id: z.string().nullish(),
    hgvsp: z.string().nullish(),
    aapos: z.number().nullish(),
    ref: z.string().nullish(),
    alt: z.string().nullish()
  }),
  variants: z.array(z.object({
    variant: variantSimplifiedFormat,
    scores: z.array(z.object({
      method: z.string(),
      score: z.number().nullish(),
      source_url: z.string().nullish()
    }))
  })).nullish()
})

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function validateInput (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['gene_id', 'hgnc_id', 'gene_name', 'alias'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one gene property must be defined.'
    })
  }
}

// ClickHouse-only gene resolver. Returns { name } or null if not found.
async function resolveGene (input: paramsFormatType): Promise<{ name: string } | null> {
  const params: QueryParams = {}
  let condition: string

  if (input.gene_id !== undefined) {
    params._gid = input.gene_id as string
    condition = 'id = {_gid:String}'
  } else if (input.gene_name !== undefined) {
    params._gname = input.gene_name as string
    condition = 'name = {_gname:String}'
  } else if (input.hgnc_id !== undefined) {
    let hgnc = input.hgnc_id as string
    if (!hgnc.startsWith('HGNC:')) hgnc = `HGNC:${hgnc}`
    params._hgnc = hgnc
    condition = 'hgnc = {_hgnc:String}'
  } else if (input.alias !== undefined) {
    params._alias = input.alias as string
    condition = 'has(synonyms, {_alias:String})'
  } else {
    return null
  }

  const rows = await chQuery<{ name: string }>(
    `SELECT name FROM genes WHERE ${condition} LIMIT 1`,
    params
  )
  return rows[0] ?? null
}

// Strip the 'variants/' collection prefix from a stored FK value.
function bareVariantId (raw: string): string {
  return raw.startsWith('variants/') ? raw.slice('variants/'.length) : raw
}

// ---------------------------------------------------------------------------
// Query: GET /genes/coding-variants/scores
// ---------------------------------------------------------------------------

async function findCodingVariantsFromGenes (input: paramsFormatType): Promise<any[]> {
  validateInput(input)

  let limit = 25
  if (input.limit !== undefined) {
    limit = (input.limit as number <= QUERY_LIMIT) ? input.limit as number : QUERY_LIMIT
  }
  const page = (input.page as number) ?? 0
  const method = input.method as string | undefined
  const filesFileset = input.files_fileset as string | undefined

  const gene = await resolveGene(input)
  if (gene === null) return []
  const { name: geneName } = gene

  // Step A: paginate at hgvsp (protein_change) level — bounds all subsequent
  // sqlInList calls to at most `limit` hgvsp strings and ~limit*10 CV IDs.
  let hgvspPage: string[]

  if (method === undefined && filesFileset === undefined) {
    // No filter: paginate directly from the coding_variants table.
    const hgvspRows = await chQuery<{ hgvsp: string }>(
      `SELECT hgvsp
       FROM coding_variants
       WHERE gene_name = {_gname:String}
       GROUP BY hgvsp
       ORDER BY min(protein_id) ASC, min(aapos) ASC
       LIMIT {_lim:UInt32} OFFSET {_off:UInt32}`,
      { _gname: geneName, _lim: limit, _off: page * limit }
    )
    hgvspPage = hgvspRows.map(r => r.hgvsp)
  } else {
    // Filtered path: find hgvsp values that have at least one CVP record
    // matching the method/fileset filters. The proj_by_cv_id projection on
    // coding_variants_phenotypes (sorted by coding_variants_id) is used to
    // efficiently restrict CVP to this gene's rows via the IN subquery.
    const filterWhere: string[] = []
    const filterParams: QueryParams = {
      _gname: geneName,
      _lim: limit,
      _off: page * limit
    }

    if (method !== undefined) {
      filterWhere.push('method = {_method:String}')
      filterParams._method = method
    }
    if (filesFileset !== undefined) {
      filterWhere.push('files_filesets = {_fileset:String}')
      filterParams._fileset = `files_filesets/${filesFileset}`
    }

    const extraWhere = filterWhere.length > 0 ? ' AND ' + filterWhere.join(' AND ') : ''

    // Two-level subquery: the inner SELECT uses the CVP proj_by_cv_id lean
    // projection (SELECT id WHERE coding_variants_id IN ... is fully in the
    // projection). The outer WHERE uses the primary key on those IDs, so
    // ClickHouse prunes to only the gene's granules before applying the filter.
    const hgvspRows = await chQuery<{ hgvsp: string }>(
      `SELECT cv.hgvsp
       FROM coding_variants cv
       WHERE cv.gene_name = {_gname:String}
         AND cv.id IN (
           SELECT DISTINCT coding_variants_id
           FROM coding_variants_phenotypes
           WHERE id IN (
             SELECT id FROM coding_variants_phenotypes
             WHERE coding_variants_id IN (
               SELECT id FROM coding_variants WHERE gene_name = {_gname:String}
             )
           )${extraWhere}
         )
       GROUP BY cv.hgvsp
       ORDER BY min(cv.protein_id) ASC, min(cv.aapos) ASC
       LIMIT {_lim:UInt32} OFFSET {_off:UInt32}`,
      filterParams
    )
    hgvspPage = hgvspRows.map(r => r.hgvsp)
  }

  if (hgvspPage.length === 0) return []

  // Step B: CV metadata for the page of hgvsp values (bounded sqlInList: ≤limit strings)
  const cvMetaRows = await chQuery<{
    cv_id: string
    protein_id: string
    protein_name: string
    transcript_id: string
    hgvsp: string
    aapos: number
    cv_ref: string
    cv_alt: string
  }>(
    `SELECT cv.id AS cv_id, cv.protein_id, cv.protein_name, cv.transcript_id,
            cv.hgvsp, cv.aapos, cv.ref AS cv_ref, cv.alt AS cv_alt
     FROM coding_variants cv
     WHERE cv.gene_name = {_gname:String}
       AND cv.hgvsp IN (${sqlInList(hgvspPage)})`,
    { _gname: geneName }
  )

  const activeCvIds = cvMetaRows.map(r => r.cv_id)
  if (activeCvIds.length === 0) return []

  const cvMeta = new Map(cvMetaRows.map(r => [r.cv_id, r]))

  // Step C: phenotype scores + variant IDs for active CV IDs.
  //
  // Two-step using the proj_by_cv_id lean projection on coding_variants_phenotypes
  // (sorted by coding_variants_id). activeCvIds is bounded to ≤limit*10 (~250) IDs.
  //
  // C1: resolve CVP primary keys via projection — SELECT id WHERE coding_variants_id IN
  // is fully satisfiable from the projection (both columns are stored there).
  //
  // cvp.variants stores the linked genomic variant ID with 'variants/' prefix
  // for records where the phenotype is directly tied to a specific variant
  // (e.g. SGE). For protein-level phenotypes (MutPred2, ESM-1v), cvp.variants
  // may be empty — those are resolved via VCV in step D.
  const cvpIdRows = await chQuery<{ id: string }>(
    `SELECT id FROM coding_variants_phenotypes
     WHERE coding_variants_id IN (${sqlInList(activeCvIds)})`
  )
  const cvpIds = cvpIdRows.map(r => r.id)

  let phenoRows: Array<{
    coding_variants_id: string
    method: string
    score_value: number
    source_url: string
    variants: string
  }> = []

  if (cvpIds.length > 0) {
    // C2: fetch full rows by primary key, applying method/fileset filters
    const phenoWhere: string[] = [`cvp.id IN (${sqlInList(cvpIds)})`]
    const phenoParams: QueryParams = {}

    if (method !== undefined) {
      phenoWhere.push('cvp.method = {_method:String}')
      phenoParams._method = method
    }
    if (filesFileset !== undefined) {
      phenoWhere.push('cvp.files_filesets = {_fileset:String}')
      phenoParams._fileset = `files_filesets/${filesFileset}`
    }

    phenoRows = await chQuery<{
      coding_variants_id: string
      method: string
      score_value: number
      source_url: string
      variants: string
    }>(
      `SELECT
        cvp.coding_variants_id,
        cvp.method,
        cvp.source_url,
        cvp.variants,
        CASE
          WHEN cvp.method = 'MutPred2' THEN cvp.pathogenicity_score
          WHEN cvp.method = 'ESM-1v'   THEN cvp.esm_1v_score
          ELSE                              cvp.score
        END AS score_value
      FROM coding_variants_phenotypes cvp
      WHERE ${phenoWhere.join(' AND ')}`,
      phenoParams
    )
  }

  // Build per-CV lookups.
  // Variant IDs from cvp.variants (populated for SGE etc.); others fall back to VCV.
  const cvToVariantId = new Map<string, string>()
  const cvToScores = new Map<string, Array<{ method: string, score: number, source_url: string | null }>>()

  for (const row of phenoRows) {
    if (row.variants !== '' && !cvToVariantId.has(row.coding_variants_id)) {
      cvToVariantId.set(row.coding_variants_id, bareVariantId(row.variants))
    }
    const list = cvToScores.get(row.coding_variants_id) ?? []
    list.push({ method: row.method, score: row.score_value, source_url: row.source_url || null })
    cvToScores.set(row.coding_variants_id, list)
  }

  // Step D: VCV lookup for CVs whose variant ID was not in cvp.variants.
  // The proj_by_cv_id lean projection on variants_coding_variants stores
  // (coding_variants_id, variants_id) sorted by coding_variants_id, which
  // fully satisfies this SELECT/WHERE — ClickHouse reads from the projection.
  const needsVcv = activeCvIds.filter(id => !cvToVariantId.has(id))
  if (needsVcv.length > 0) {
    const vcvRows = await chQuery<{ variants_id: string, coding_variants_id: string }>(
      `SELECT vcv.variants_id, vcv.coding_variants_id
       FROM variants_coding_variants vcv
       WHERE vcv.coding_variants_id IN (${sqlInList(needsVcv)})
       LIMIT 1 BY vcv.coding_variants_id`
    )
    for (const row of vcvRows) {
      cvToVariantId.set(row.coding_variants_id, row.variants_id)
    }
  }

  // Step E: fetch simplified variant objects for all unique genomic variant IDs
  const uniqueVariantIds = Array.from(new Set(cvToVariantId.values()))
  const variantMap = new Map<string, any>()
  if (uniqueVariantIds.length > 0) {
    const variantRows = await chQuery<any>(
      `SELECT ${VARIANT_SIMPLIFIED_SELECT} FROM variants v WHERE v.id IN (${sqlInList(uniqueVariantIds)})`
    )
    for (const row of variantRows) variantMap.set(row._id, row)
  }

  // Step F: assemble output preserving hgvspPage order.
  const hgvspToCvIds = new Map<string, string[]>()
  for (const row of cvMetaRows) {
    const cvList = hgvspToCvIds.get(row.hgvsp) ?? []
    cvList.push(row.cv_id)
    hgvspToCvIds.set(row.hgvsp, cvList)
  }

  return hgvspPage
    .filter(hgvsp => hgvspToCvIds.has(hgvsp))
    .map(hgvsp => {
      const cvIds = hgvspToCvIds.get(hgvsp) ?? []
      const meta = cvMeta.get(cvIds[0])!

      // Deduplicate variants within this protein_change group by variant ID,
      // merging scores from multiple coding variants that share the same
      // genomic variant.
      const variantToScores = new Map<string, { variant: any, scores: any[] }>()
      for (const cvId of cvIds) {
        const variantId = cvToVariantId.get(cvId)
        if (variantId === undefined) continue
        const variant = variantMap.get(variantId)
        if (variant === undefined) continue
        const scores = cvToScores.get(cvId) ?? []

        const existing = variantToScores.get(variantId)
        if (existing === undefined) {
          variantToScores.set(variantId, { variant, scores: scores.slice() })
        } else {
          // Multiple coding variants can share the same hgvsp and genomic variant
          // (e.g. different transcripts). Deduplicate by (method, source_url) so
          // the same score is not listed twice. The number of scores per variant
          // is bounded (≤ #methods × #filesets), so a linear scan is fine.
          for (const s of scores) {
            if (!existing.scores.some(e => e.method === s.method && e.source_url === s.source_url)) {
              existing.scores.push(s)
            }
          }
        }
      }

      return {
        protein_change: {
          coding_variant_id: meta.cv_id,
          protein_id: meta.protein_id || null,
          protein_name: meta.protein_name || null,
          transcript_id: meta.transcript_id || null,
          hgvsp: meta.hgvsp || null,
          aapos: meta.aapos ?? null,
          ref: meta.cv_ref || null,
          alt: meta.cv_alt || null
        },
        variants: Array.from(variantToScores.values())
      }
    })
}

// ---------------------------------------------------------------------------
// Query: GET /genes/coding-variants/all-scores
// ---------------------------------------------------------------------------

async function findAllCodingVariantsFromGenes (input: paramsFormatType): Promise<any[]> {
  if (input.gene_id === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'gene_id is required'
    })
  }

  let limit = 500
  if (input.limit !== undefined) {
    limit = (input.limit as number <= QUERY_LIMIT) ? input.limit as number : QUERY_LIMIT
  }
  const page = (input.page as number) ?? 0
  const dataset = input.dataset as string

  // Score column from static map — never interpolated from raw user input
  const scoreCol = DATASET_SCORE_COL[dataset]
  if (scoreCol === undefined) {
    throw new TRPCError({ code: 'BAD_REQUEST', message: `Unknown dataset: ${dataset}` })
  }

  // Resolve gene name (chr not needed for this endpoint)
  const geneRows = await chQuery<{ name: string }>(
    'SELECT name FROM genes WHERE id = {_gid:String} LIMIT 1',
    { _gid: input.gene_id as string }
  )
  const geneName = geneRows[0]?.name
  if (geneName === undefined) return []

  // Two-level subquery: inner uses proj_by_cv_id lean projection to resolve
  // CVP primary keys by coding_variants_id. Outer uses those IDs as a primary
  // key filter — ClickHouse's min/max pruning restricts reads to the gene's
  // contiguous block in the main table before applying the method filter.
  const scoreRows = await chQuery<{ score_value: number }>(
    `SELECT cvp.${scoreCol} AS score_value
     FROM coding_variants_phenotypes cvp
     WHERE cvp.id IN (
       SELECT id FROM coding_variants_phenotypes
       WHERE coding_variants_id IN (
         SELECT id FROM coding_variants WHERE gene_name = {_gname:String}
       )
     )
     AND cvp.method = {_method:String}
     ORDER BY cvp.${scoreCol} DESC
     LIMIT {_lim:UInt32} OFFSET {_off:UInt32}`,
    { _gname: geneName, _method: dataset, _lim: limit, _off: page * limit }
  )

  return scoreRows.map(r => r.score_value)
}

// ---------------------------------------------------------------------------
// tRPC route definitions
// ---------------------------------------------------------------------------

const codingVariantsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/coding-variants/scores', description: descriptions.genes_coding_variants } })
  .input(geneQueryFormat)
  .output(z.array(codingVariantsScoresFormat))
  .query(async ({ input }) => await findCodingVariantsFromGenes(input))

const allCodingVariantsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/coding-variants/all-scores', description: descriptions.genes_coding_variants } })
  .input(allVariantsQueryFormat)
  .output(z.array(z.number().optional()))
  .query(async ({ input }) => await findAllCodingVariantsFromGenes(input))

export const genesCodingVariantsRouters = {
  codingVariantsFromGenes,
  allCodingVariantsFromGenes
}
