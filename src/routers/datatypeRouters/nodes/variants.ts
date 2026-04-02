import { z } from 'zod'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { validRegion, distanceGeneVariant } from '../_helpers'
import type { paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { nearestGeneSearch } from './genes'
import { commonHumanNodesParamsFormat, commonNodesParamsFormat, variantsCommonQueryFormat } from '../params'
import {
  chQuery, getChSelectStatements, getChFilterConditions,
  getChTableSchema, loadJsonSchema, type QueryParams
} from '../clickhouse_helpers'
import { getCollectionEnumValuesOrThrow } from '../schema'

const TABLE = 'variants'
const MAX_PAGE_SIZE = 500
const MOUSE_STRAINS = getCollectionEnumValuesOrThrow('nodes', 'mm_variants', 'strain')

// ---------------------------------------------------------------------------
// Schemas (loaded once at import time)
// ---------------------------------------------------------------------------

const variantsChSchema = getChTableSchema('variants')
const favorSchema = loadJsonSchema('nodes/variants.Favor.json')

const VARIANT_SELECT = getChSelectStatements(favorSchema, variantsChSchema, 'v')

const frequencySources = z.enum([
  'bravo_af',
  'gnomad_af_total',
  'gnomad_af_afr',
  'gnomad_af_afr_female',
  'gnomad_af_afr_male',
  'gnomad_af_ami',
  'gnomad_af_ami_female',
  'gnomad_af_ami_male',
  'gnomad_af_amr',
  'gnomad_af_amr_female',
  'gnomad_af_amr_male',
  'gnomad_af_asj',
  'gnomad_af_asj_female',
  'gnomad_af_asj_male',
  'gnomad_af_eas',
  'gnomad_af_eas_female',
  'gnomad_af_eas_male',
  'gnomad_af_female',
  'gnomad_af_fin',
  'gnomad_af_fin_female',
  'gnomad_af_fin_male',
  'gnomad_af_male',
  'gnomad_af_nfe',
  'gnomad_af_nfe_female',
  'gnomad_af_nfe_male',
  'gnomad_af_oth',
  'gnomad_af_oth_female',
  'gnomad_af_oth_male',
  'gnomad_af_sas',
  'gnomad_af_sas_male',
  'gnomad_af_sas_female',
  'gnomad_af_raw'
])

const variantsFromRegionsFormat = z.object({
  region: z.string().trim().optional()
})

export const singleVariantQueryFormat = z.object({
  spdi: z.string().trim().optional(),
  hgvs: z.string().trim().optional(),
  ca_id: z.string().trim().optional(),
  variant_id: z.string().trim().optional(),
  organism: z.enum(['Mus musculus', 'Homo sapiens']).default('Homo sapiens')
})

const variantsSummaryFormat = z.object({
  summary: z.object({
    rsid: z.array(z.string()).nullish(),
    varinfo: z.string().nullish(),
    spdi: z.string().nullish(),
    hgvs: z.string().nullish(),
    ca_id: z.string().nullish(),
    ref: z.string().nullish(),
    alt: z.string().nullish()
  }),
  allele_frequencies_gnomad: z.any(),
  cadd_scores: z.object({
    raw: z.number().nullish(),
    phread: z.number().nullish()
  }).nullish(),
  nearest_genes: z.object({
    nearestCodingGene: z.object({
      gene_name: z.string().nullish(),
      id: z.string(),
      start: z.number(),
      end: z.number(),
      distance: z.number()
    }),
    nearestGene: z.object({
      gene_name: z.string().nullish(),
      id: z.string(),
      start: z.number(),
      end: z.number(),
      distance: z.number()
    })
  })
})

const variantsQueryFormat = variantsCommonQueryFormat.merge(z.object({
  GENCODE_category: z.enum(['coding', 'noncoding']).optional(),
  mouse_strain: z.enum(MOUSE_STRAINS).optional()
})).merge(commonNodesParamsFormat)

const variantsFreqQueryFormat = z.object({
  source: frequencySources,
  spdi: z.string().trim().optional(),
  hgvs: z.string().trim().optional(),
  rsid: z.string().trim().optional(),
  ca_id: z.string().trim().optional(),
  region: z.string().trim().optional(),
  GENCODE_category: z.enum(['coding', 'noncoding']).optional(),
  minimum_af: z.number().default(0),
  maximum_af: z.number().default(1)
}).merge(commonHumanNodesParamsFormat)

export const variantFormat = z.object({
  _id: z.string(),
  chr: z.string(),
  pos: z.number(),
  rsid: z.array(z.string()).nullish(),
  ref: z.string(),
  alt: z.string(),
  spdi: z.string().optional(),
  hgvs: z.string().optional(),
  ca_id: z.string().nullish(),
  strain: z.array(z.string()).nullish(),
  qual: z.string().nullish(),
  filter: z.string().nullish(),
  files_filesets: z.string().nullish(),
  annotations: z.object({
    bravo_af: z.number().nullish(),
    gnomad_af_total: z.number().nullish(),
    gnomad_af_afr: z.number().nullish(),
    gnomad_af_afr_female: z.number().nullish(),
    gnomad_af_afr_male: z.number().nullish(),
    gnomad_af_ami: z.number().nullish(),
    gnomad_af_ami_female: z.number().nullish(),
    gnomad_af_ami_male: z.number().nullish(),
    gnomad_af_amr: z.number().nullish(),
    gnomad_af_amr_female: z.number().nullish(),
    gnomad_af_amr_male: z.number().nullish(),
    gnomad_af_asj: z.number().nullish(),
    gnomad_af_asj_female: z.number().nullish(),
    gnomad_af_asj_male: z.number().nullish(),
    gnomad_af_eas: z.number().nullish(),
    gnomad_af_eas_female: z.number().nullish(),
    gnomad_af_eas_male: z.number().nullish(),
    gnomad_af_female: z.number().nullish(),
    gnomad_af_fin: z.number().nullish(),
    gnomad_af_fin_female: z.number().nullish(),
    gnomad_af_fin_male: z.number().nullish(),
    gnomad_af_male: z.number().nullish(),
    gnomad_af_nfe: z.number().nullish(),
    gnomad_af_nfe_female: z.number().nullish(),
    gnomad_af_nfe_male: z.number().nullish(),
    gnomad_af_oth: z.number().nullish(),
    gnomad_af_oth_female: z.number().nullish(),
    gnomad_af_oth_male: z.number().nullish(),
    gnomad_af_sas: z.number().nullish(),
    gnomad_af_sas_male: z.number().nullish(),
    gnomad_af_sas_female: z.number().nullish(),
    gnomad_af_raw: z.number().nullish(),
    GENCODE_category: z.string().nullish(),
    funseq_description: z.string().nullish()
  }).nullable(),
  source: z.string(),
  source_url: z.string(),
  organism: z.string().nullable()
}).transform(({ organism, ...rest }) => ({
  organism: organism ?? 'Homo sapiens',
  ...rest
}))
type variantType = z.infer<typeof variantFormat>

export const variantSimplifiedFormat = z.object({
  chr: z.string(),
  pos: z.number(),
  ref: z.string(),
  alt: z.string(),
  rsid: z.array(z.string()).nullish(),
  spdi: z.string().nullish(),
  hgvs: z.string().nullish(),
  ca_id: z.string().nullish(),
  _id: z.string().optional()
})

// ---------------------------------------------------------------------------
// ClickHouse SQL helpers
// ---------------------------------------------------------------------------

function parseRegion (region: string): { chr: string, start: number, end: number } {
  const breakdown = validRegion(region)
  if (breakdown == null) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Region format invalid. Please use the format as the example: "chr2:12345-54321". The end position must be greater than the start position.'
    })
  }
  return { chr: breakdown[1], start: parseInt(breakdown[2]), end: parseInt(breakdown[3]) }
}

function buildVariantWhere (input: paramsFormatType, params: QueryParams): string {
  const conds: string[] = []

  // variant_id -> id column (name mismatch, explicit handling)
  if (input.variant_id !== undefined) {
    conds.push('v.id = {_variant_id:String}')
    params._variant_id = input.variant_id as string
  }

  // Schema-driven simple equality/array filters: spdi, hgvs, ca_id, rsid
  const simpleFilters: Record<string, string | undefined> = {}
  if (input.spdi !== undefined) simpleFilters.spdi = input.spdi as string
  if (input.hgvs !== undefined) simpleFilters.hgvs = input.hgvs as string
  if (input.ca_id !== undefined) simpleFilters.ca_id = input.ca_id as string
  if (input.rsid !== undefined) simpleFilters.rsid = input.rsid as string

  const schemaConds = getChFilterConditions(favorSchema, variantsChSchema, simpleFilters, 'v', params)
  conds.push(...schemaConds)

  // Region filter (complex, explicit handling with parameterized values)
  if (input.region !== undefined) {
    const r = parseRegion(input.region as string)
    conds.push('v.chr = {_region_chr:String}')
    params._region_chr = r.chr
    conds.push('v.pos >= {_region_start:Float64}')
    params._region_start = r.start
    conds.push('v.pos < {_region_end:Float64}')
    params._region_end = r.end
  }

  // Annotation-specific filters (JSON path, domain-specific)
  if (input.GENCODE_category !== undefined) {
    conds.push('v.annotations.funseq_description = {_gencode:String}')
    params._gencode = input.GENCODE_category as string
  }

  // Frequency source filter — field name is from Zod enum (safe), values are parameterized
  if (input.source !== undefined) {
    const dbField = (input.source as string).replace('gnomad_', '')
    conds.push(`v.annotations.${dbField} >= {_min_af:Float64}`)
    params._min_af = (input.minimum_af as number) ?? 0
    conds.push(`v.annotations.${dbField} < {_max_af:Float64}`)
    params._max_af = (input.maximum_af as number) ?? 1
  }

  return conds.length > 0 ? `WHERE ${conds.join(' AND ')}` : ''
}

function transformAnnotations (raw: any): any {
  if (raw == null) return null
  return {
    bravo_af: raw.bravo_af ?? null,
    gnomad_af_total: raw.af_total ?? null,
    gnomad_af_afr: raw.af_afr ?? null,
    gnomad_af_afr_female: raw.af_afr_female ?? null,
    gnomad_af_afr_male: raw.af_afr_male ?? null,
    gnomad_af_ami: raw.af_ami ?? null,
    gnomad_af_ami_female: raw.af_ami_female ?? null,
    gnomad_af_ami_male: raw.af_ami_male ?? null,
    gnomad_af_amr: raw.af_amr ?? null,
    gnomad_af_amr_female: raw.af_amr_female ?? null,
    gnomad_af_amr_male: raw.af_amr_male ?? null,
    gnomad_af_asj: raw.af_asj ?? null,
    gnomad_af_asj_female: raw.af_asj_female ?? null,
    gnomad_af_asj_male: raw.af_asj_male ?? null,
    gnomad_af_eas: raw.af_eas ?? null,
    gnomad_af_eas_female: raw.af_eas_female ?? null,
    gnomad_af_eas_male: raw.af_eas_male ?? null,
    gnomad_af_female: raw.af_female ?? null,
    gnomad_af_fin: raw.af_fin ?? null,
    gnomad_af_fin_female: raw.af_fin_female ?? null,
    gnomad_af_fin_male: raw.af_fin_male ?? null,
    gnomad_af_male: raw.af_male ?? null,
    gnomad_af_nfe: raw.af_nfe ?? null,
    gnomad_af_nfe_female: raw.af_nfe_female ?? null,
    gnomad_af_nfe_male: raw.af_nfe_male ?? null,
    gnomad_af_oth: raw.af_oth ?? null,
    gnomad_af_oth_female: raw.af_oth_female ?? null,
    gnomad_af_oth_male: raw.af_oth_male ?? null,
    gnomad_af_sas: raw.af_sas ?? null,
    gnomad_af_sas_male: raw.af_sas_male ?? null,
    gnomad_af_sas_female: raw.af_sas_female ?? null,
    gnomad_af_raw: raw.af_raw ?? null,
    cadd_rawscore: raw.cadd_rawscore ?? null,
    cadd_phred: raw.cadd_phred ?? null,
    GENCODE_category: raw.funseq_description ?? null,
    funseq_description: raw.funseq_description ?? null
  }
}

function transformVariantRow (row: any): any {
  const annotations = typeof row.annotations === 'string'
    ? JSON.parse(row.annotations)
    : (row.annotations ?? null)

  return {
    _id: row._id,
    chr: row.chr,
    pos: row.pos,
    rsid: row.rsid ?? null,
    ref: row.ref,
    alt: row.alt,
    spdi: row.spdi || undefined,
    hgvs: row.hgvs || undefined,
    ca_id: row.ca_id || null,
    qual: row.qual || null,
    filter: row.filter ?? null,
    files_filesets: row.files_filesets || null,
    annotations: transformAnnotations(annotations),
    source: row.source,
    source_url: row.source_url,
    organism: row.organism || 'Homo sapiens'
  }
}

// ---------------------------------------------------------------------------
// Query functions
// ---------------------------------------------------------------------------

export async function findVariantIDBySpdi (spdi: string): Promise<string | null> {
  const rows = await chQuery<{ id: string }>(
    `SELECT id FROM ${TABLE} WHERE spdi = {_spdi:String} LIMIT 1`,
    { _spdi: spdi }
  )
  return rows[0]?.id ?? null
}

export async function findVariantIDByRSID (rsid: string): Promise<string[]> {
  const rows = await chQuery<{ id: string }>(
    `SELECT id FROM ${TABLE} WHERE has(rsid, {_rsid:String})`,
    { _rsid: rsid }
  )
  return rows.map(r => r.id)
}

export async function findVariantIDByHgvs (hgvs: string): Promise<string | null> {
  const rows = await chQuery<{ id: string }>(
    `SELECT id FROM ${TABLE} WHERE hgvs = {_hgvs:String} LIMIT 1`,
    { _hgvs: hgvs }
  )
  return rows[0]?.id ?? null
}

export async function findVariantIDsByRegion (region: string): Promise<string[]> {
  const r = parseRegion(region)
  const rows = await chQuery<{ id: string }>(
    `SELECT id FROM ${TABLE} WHERE chr = {_chr:String} AND pos >= {_start:Float64} AND pos < {_end:Float64}`,
    { _chr: r.chr, _start: r.start, _end: r.end }
  )
  return rows.map(row => row.id)
}

export function preProcessVariantParams (input: paramsFormatType): paramsFormatType {
  return input
}

export async function variantSearch (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  delete input.mouse_strain

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = Math.min(input.limit as number, MAX_PAGE_SIZE)
    delete input.limit
  }

  const page = (input.page as number) ?? 0
  delete input.page

  const params: QueryParams = {}
  const where = buildVariantWhere(input, params)
  params._lim = limit
  params._off = page * limit
  const sql = `SELECT ${VARIANT_SELECT} FROM ${TABLE} v ${where} ORDER BY v.id LIMIT {_lim:UInt32} OFFSET {_off:UInt32}`

  const rows = await chQuery(sql, params)
  return rows.map(transformVariantRow)
}

async function nearestGenes (variant: variantType): Promise<any> {
  let nearestGene, distNearestGene, nearestCodingGene, distCodingGene

  const genes = await nearestGeneSearch({ region: `${variant.chr}:${variant.pos}-${variant.pos + 1}` })

  if (variant.annotations?.funseq_description === 'coding') {
    nearestGene = genes[0]
    distNearestGene = distanceGeneVariant(nearestGene.start, nearestGene.end, variant.pos)

    for (let index = 1; index < genes.length; index++) {
      const newDistance = distanceGeneVariant(genes[index].start, genes[index].end, variant.pos)
      if (newDistance < distNearestGene) {
        distNearestGene = newDistance
        nearestGene = genes[index]
      }
    }

    nearestCodingGene = nearestGene
    distCodingGene = distNearestGene
  } else {
    const nearestCodingGenes = await nearestGeneSearch({ gene_type: 'protein_coding', region: `${variant.chr}:${variant.pos}-${variant.pos + 1}` })

    nearestGene = genes[0]
    distNearestGene = distanceGeneVariant(genes[0].start, genes[0].end, variant.pos)
    if (genes.length > 1) {
      const distGene1 = distanceGeneVariant(genes[1].start, genes[1].end, variant.pos)
      if (distGene1 < distNearestGene) {
        nearestGene = genes[1]
        distNearestGene = distGene1
      }
    }

    nearestCodingGene = nearestCodingGenes[0]
    distCodingGene = distanceGeneVariant(nearestCodingGenes[0].start, nearestCodingGenes[0].end, variant.pos)
    if (nearestCodingGenes.length > 1) {
      const distGene1 = distanceGeneVariant(nearestCodingGenes[1].start, nearestCodingGenes[1].end, variant.pos)
      if (distGene1 < distCodingGene) {
        nearestCodingGene = nearestCodingGenes[1]
        distCodingGene = distGene1
      }
    }
  }

  return {
    nearestCodingGene: {
      gene_name: nearestCodingGene.name,
      id: nearestCodingGene._id,
      start: nearestCodingGene.start,
      end: nearestCodingGene.end,
      distance: distCodingGene
    },
    nearestGene: {
      gene_name: nearestGene.name,
      id: nearestGene._id,
      start: nearestGene.start,
      end: nearestGene.end,
      distance: distNearestGene
    }
  }
}

async function variantSummarySearch (input: paramsFormatType): Promise<any> {
  input.page = 0
  const variant = (await variantSearch(input))[0]

  if (variant === undefined) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Variant not found.'
    })
  }

  return {
    summary: {
      rsid: variant.rsid,
      varinfo: variant.annotations?.varinfo,
      spdi: variant.spdi,
      hgvs: variant.hgvs,
      ref: variant.ref,
      alt: variant.alt,
      ca_id: variant.ca_id,
      pos: variant.pos
    },
    allele_frequencies_gnomad: {
      total: variant.annotations?.gnomad_af_total,
      male: variant.annotations?.gnomad_af_male,
      female: variant.annotations?.gnomad_af_female,
      raw: variant.annotations?.gnomad_af_raw,
      african: {
        total: variant.annotations?.gnomad_af_afr,
        male: variant.annotations?.gnomad_af_afr_male,
        female: variant.annotations?.gnomad_af_afr_female
      },
      amish: {
        total: variant.annotations?.gnomad_af_ami,
        male: variant.annotations?.gnomad_af_ami_male,
        female: variant.annotations?.gnomad_af_ami_female
      },
      ashkenazi_jewish: {
        total: variant.annotations?.gnomad_af_asj,
        male: variant.annotations?.gnomad_af_asj_male,
        female: variant.annotations?.gnomad_af_asj_female
      },
      east_asian: {
        total: variant.annotations?.gnomad_af_eas,
        male: variant.annotations?.gnomad_af_eas_male,
        female: variant.annotations?.gnomad_af_eas_female
      },
      finnish: {
        total: variant.annotations?.gnomad_af_fin,
        male: variant.annotations?.gnomad_af_fin_male,
        female: variant.annotations?.gnomad_af_fin_female
      },
      native_american: {
        total: variant.annotations?.gnomad_af_amr,
        male: variant.annotations?.gnomad_af_amr_male,
        female: variant.annotations?.gnomad_af_amr_female
      },
      non_finnish_european: {
        total: variant.annotations?.gnomad_af_nfe,
        male: variant.annotations?.gnomad_af_nfe_male,
        female: variant.annotations?.gnomad_af_nfe_female
      },
      other: {
        total: variant.annotations?.gnomad_af_oth,
        male: variant.annotations?.gnomad_af_oth_male,
        female: variant.annotations?.gnomad_af_oth_female
      },
      south_asian: {
        total: variant.annotations?.gnomad_af_sas,
        male: variant.annotations?.gnomad_af_sas_male,
        female: variant.annotations?.gnomad_af_sas_female
      }
    },
    cadd_scores: {
      raw: variant.annotations?.cadd_rawscore,
      phread: variant.annotations?.cadd_phred
    },
    nearest_genes: await nearestGenes(variant)
  }
}

export async function variantIDSearch (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  delete input.mouse_strain

  if (input.chr !== undefined && input.position !== undefined) {
    input.region = `${input.chr as string}:${input.position as string}-${parseInt(input.position as string) + 1}`
    delete input.chr
    delete input.position
  }

  if (input.region !== undefined) {
    const coords = (input.region as string).split(':')[1]
    const startEnd = coords.split('-')
    if (parseInt(startEnd[1]) - parseInt(startEnd[0]) > 10000) {
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: 'Region span exceeds 10kb.'
      })
    }
  }

  const params: QueryParams = {}
  const where = buildVariantWhere(input, params)
  if (where === '') return []

  const sql = `SELECT v.id FROM ${TABLE} v ${where}`
  const rows = await chQuery<{ id: string }>(sql, params)
  return rows.map(r => r.id)
}

export async function findVariants (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  delete input.mouse_strain

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = Math.min(input.limit as number, MAX_PAGE_SIZE)
    delete input.limit
  }

  const page = (input.page as number) ?? 0
  delete input.page

  const params: QueryParams = {}
  const where = buildVariantWhere(input, params)
  params._lim = limit
  params._off = page * limit
  const sql = `SELECT ${VARIANT_SELECT} FROM ${TABLE} v ${where} ORDER BY v.id LIMIT {_lim:UInt32} OFFSET {_off:UInt32}`

  const rows = await chQuery(sql, params)
  return rows.map(transformVariantRow)
}

async function variantsAllelesAggregation (input: paramsFormatType): Promise<any[]> {
  const invalidCallMessage = 'A valid region must be defined. Max interval: 1kb.'

  let validInput = false
  if (input.region !== undefined) {
    const breakdown = validRegion(input.region as string) as string[]
    if ((breakdown !== null) && ((parseInt(breakdown[3]) - parseInt(breakdown[2])) <= 1000)) {
      validInput = true
    }
  }

  if (!validInput) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: invalidCallMessage
    })
  }

  const r = parseRegion(input.region as string)
  const sql = `
    SELECT
      chr,
      pos,
      annotations.af_afr AS af_afr,
      annotations.af_ami AS af_ami,
      annotations.af_amr AS af_amr,
      annotations.af_asj AS af_asj,
      annotations.af_eas AS af_eas,
      annotations.af_fin AS af_fin,
      annotations.af_nfe AS af_nfe,
      annotations.af_sas AS af_sas
    FROM ${TABLE}
    WHERE chr = {_chr:String} AND pos >= {_start:Float64} AND pos < {_end:Float64}
  `

  const rows = await chQuery(sql, { _chr: r.chr, _start: r.start, _end: r.end })

  if (rows.length === 0) return []

  const header = ['chr', 'pos', 'afr', 'ami', 'amr', 'asj', 'eas', 'fin', 'nfe', 'sas']
  const alleles = rows.map(row => [
    row.chr, row.pos,
    row.af_afr, row.af_ami, row.af_amr, row.af_asj,
    row.af_eas, row.af_fin, row.af_nfe, row.af_sas
  ])

  return [header].concat(alleles)
}

// ---------------------------------------------------------------------------
// tRPC route definitions
// ---------------------------------------------------------------------------

const variants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants', description: descriptions.variants } })
  .input(variantsQueryFormat)
  .output(z.array(variantFormat))
  .query(async ({ input }) => await variantSearch(input))

const variantByFrequencySource = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/freq', description: descriptions.variants_by_freq } })
  .input(variantsFreqQueryFormat)
  .output(z.array(variantFormat))
  .query(async ({ input }) => await variantSearch(input))

const variantSummary = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/summary', description: descriptions.variants_summary } })
  .input(singleVariantQueryFormat)
  .output(variantsSummaryFormat)
  .query(async ({ input }) => await variantSummarySearch(input))

const variantsAlleles = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/gnomad-alleles', description: descriptions.variants_alleles } })
  .input(variantsFromRegionsFormat)
  .output(z.array(z.array(z.string().or(z.number()).nullish())))
  .query(async ({ input }) => await variantsAllelesAggregation(input))

export const variantsRouters = {
  variantSummary,
  variantByFrequencySource,
  variants,
  variantsAlleles
}
