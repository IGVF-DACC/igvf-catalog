import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { preProcessRegionParam, paramsFormatType, getFilterStatements, getDBReturnStatements, distanceGeneVariant, validRegion } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { nearestGeneSearch } from './genes'
import { commonHumanNodesParamsFormat, commonNodesParamsFormat, variantsCommonQueryFormat } from '../params'

const MAX_PAGE_SIZE = 500
const INDEX_MDI_POS = 'idx_zkd_pos'

const schema = loadSchemaConfig()
const humanVariantSchema = schema['sequence variant']
const mouseVariantSchema = schema['sequence variant mouse']

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

// af_ frequencies have no 'gnomad_' prefix in the database, removing prefixes for queries
const frequenciesReturn = []
for (const frequency in frequencySources.Values) {
  frequenciesReturn.push(`${frequency}: record['annotations']['${frequency.replace('gnomad_', '')}']`)
}
const frequenciesDBReturn = `'annotations': { ${frequenciesReturn.join(',')}, 'cadd_rawscore': record['annotations']['cadd_rawscore'], 'cadd_phred': record['annotations']['cadd_phred'], 'GENCODE_category': record['annotations']['funseq_description'] }`

const variantsFromRegionsFormat = z.object({
  region: z.string().trim().optional()
})

export const singleVariantQueryFormat = z.object({
  spdi: z.string().trim().optional(),
  hgvs: z.string().trim().optional(),
  variant_id: z.string().trim().optional(),
  organism: z.enum(['Mus musculus', 'Homo sapiens']).default('Homo sapiens')
})

const variantsSummaryFormat = z.object({
  summary: z.object({
    rsid: z.array(z.string()).nullish(),
    varinfo: z.string().nullish(),
    spdi: z.string().nullish(),
    hgvs: z.string().nullish(),
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

const variantsQueryFormat = variantsCommonQueryFormat.omit({ chr: true, position: true }).merge(z.object({
  region: z.string().trim().optional(),
  GENCODE_category: z.enum(['coding', 'noncoding']).optional(),
  mouse_strain: z.enum(['129S1_SvImJ', 'A_J', 'CAST_EiJ', 'NOD_ShiLtJ', 'NZO_HlLtJ', 'PWK_PhJ', 'WSB_EiJ']).optional()
})).merge(commonNodesParamsFormat)

const variantsFreqQueryFormat = z.object({
  source: frequencySources,
  spdi: z.string().trim().optional(),
  hgvs: z.string().trim().optional(),
  rsid: z.string().trim().optional(),
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
  strain: z.string().nullish(),
  qual: z.string().nullish(),
  filter: z.string().nullish(),
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
  // this is a temporary solution, we will add the organism property for human variants when reloading the collection
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
  _id: z.string().optional()
})

export async function findVariantIDBySpdi (spdi: string): Promise<string | null> {
  const query = `
    FOR record in ${humanVariantSchema.db_collection_name as string}
    FILTER record.spdi == '${spdi}'
    LIMIT 1
    RETURN record._id
  `
  return (await (await db.query(query)).all())[0]
}

export async function findVariantIDByRSID (rsid: string): Promise<string[]> {
  const query = `
    FOR record in ${humanVariantSchema.db_collection_name as string}
    FILTER '${rsid}' IN record.rsid
    RETURN record._id
  `
  return await (await db.query(query)).all()
}

export async function findVariantIDByHgvs (hgvs: string): Promise<string | null> {
  const query = `
    FOR record in ${humanVariantSchema.db_collection_name as string}
    FILTER record.hgvs == '${hgvs}'
    LIMIT 1
    RETURN record._id
  `
  return (await (await db.query(query)).all())[0]
}

export async function findVariantIDsByRegion (region: string): Promise<string[]> {
  const query = `
    FOR record in ${humanVariantSchema.db_collection_name as string} OPTIONS { indexHint: "${INDEX_MDI_POS}", forceIndexHint: true }
    FILTER ${getFilterStatements(humanVariantSchema, preProcessRegionParam({ region }, 'pos'))}
    RETURN record._id
  `
  return (await (await db.query(query)).all())
}

function preProcessVariantParams (input: paramsFormatType): paramsFormatType {
  if (input.variant_id !== undefined) {
    input._key = input.variant_id
    delete input.variant_id
  }

  if (input.GENCODE_category !== undefined) {
    input['annotations.funseq_description'] = input.GENCODE_category
    delete input.GENCODE_category
  }

  if (input.mouse_strain !== undefined) {
    input.strain = input.mouse_strain
    delete input.mouse_strain
  }

  if (input.source !== undefined) {
    input[`annotations.${(input.source as string).replace('gnomad_', '')}`] = `range:${input.minimum_af as string}-${input.maximum_af as string}`
    delete input.minimum_af
    delete input.maximum_af
    delete input.source
  }
  return preProcessRegionParam(input, 'pos')
}

export async function variantSearch (input: paramsFormatType): Promise<any[]> {
  let variantSchema = humanVariantSchema
  if (input.organism === 'Mus musculus') {
    variantSchema = mouseVariantSchema

    // unsupported for mm_variants
    delete input.GENCODE_category
  }
  delete input.organism

  let useIndex = ''
  if (input.region !== undefined) {
    useIndex = `OPTIONS { indexHint: "${INDEX_MDI_POS}", forceIndexHint: true }`
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filterBy = ''
  const filterSts = getFilterStatements(variantSchema, preProcessVariantParams(input))
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }

  const query = `
    FOR record IN ${variantSchema.db_collection_name as string} ${useIndex}
    ${filterBy}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(variantSchema, false, frequenciesDBReturn, ['annotations'])} }
  `
  return await (await db.query(query)).all()
}

async function nearestGenes (variant: variantType): Promise<any> {
  let nearestGene, distNearestGene, nearestCodingGene, distCodingGene

  const nearestGenes = await nearestGeneSearch({ region: `${variant.chr}:${variant.pos}-${variant.pos + 1}` })

  if (variant.annotations.funseq_description === 'coding') {
    nearestGene = nearestGenes[0]
    distNearestGene = distanceGeneVariant(nearestGene.start, nearestGene.end, variant.pos)

    for (let index = 1; index < nearestGenes.length; index++) {
      const newDistance = distanceGeneVariant(nearestGenes[index].start, nearestGenes[index].end, variant.pos)
      if (newDistance < distNearestGene) {
        distNearestGene = newDistance
        nearestGene = nearestGenes[index]
      }
    }

    // nearestGene and nearestCodingGene are the same for coding variants
    nearestCodingGene = nearestGene
    distCodingGene = distNearestGene
  } else {
    const nearestCodingGenes = await nearestGeneSearch({ gene_type: 'protein_coding', region: `${variant.chr}:${variant.pos}-${variant.pos + 1}` })

    nearestGene = nearestGenes[0]
    distNearestGene = distanceGeneVariant(nearestGenes[0].start, nearestGenes[0].end, variant.pos)
    if (nearestGenes.length > 1) {
      const distGene1 = distanceGeneVariant(nearestGenes[1].start, nearestGenes[1].end, variant.pos)
      if (distGene1 < distNearestGene) {
        nearestGene = nearestGenes[1]
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
      varinfo: variant.annotations.varinfo,
      spdi: variant.spdi,
      hgvs: variant.hgvs,
      ref: variant.ref,
      alt: variant.alt,
      pos: variant.pos
    },
    allele_frequencies_gnomad: {
      total: variant.annotations.gnomad_af_total,
      male: variant.annotations.gnomad_af_male,
      female: variant.annotations.gnomad_af_female,
      raw: variant.annotations.gnomad_af_raw,
      african: {
        total: variant.annotations.gnomad_af_afr,
        male: variant.annotations.gnomad_af_afr_male,
        female: variant.annotations.gnomad_af_afr_female
      },
      amish: {
        total: variant.annotations.gnomad_af_ami,
        male: variant.annotations.gnomad_af_ami_male,
        female: variant.annotations.gnomad_af_ami_female
      },
      ashkenazi_jewish: {
        total: variant.annotations.gnomad_af_asj,
        male: variant.annotations.gnomad_af_asj_male,
        female: variant.annotations.gnomad_af_asj_female
      },
      east_asian: {
        total: variant.annotations.gnomad_af_eas,
        male: variant.annotations.gnomad_af_eas_male,
        female: variant.annotations.gnomad_af_eas_female
      },
      finnish: {
        total: variant.annotations.gnomad_af_fin,
        male: variant.annotations.gnomad_af_fin_male,
        female: variant.annotations.gnomad_af_fin_female
      },
      native_american: {
        total: variant.annotations.gnomad_af_amr,
        male: variant.annotations.gnomad_af_amr_male,
        female: variant.annotations.gnomad_af_amr_female
      },
      non_finnish_european: {
        total: variant.annotations.gnomad_af_nfe,
        male: variant.annotations.gnomad_af_nfe_male,
        female: variant.annotations.gnomad_af_nfe_female
      },
      other: {
        total: variant.annotations.gnomad_af_oth,
        male: variant.annotations.gnomad_af_oth_male,
        female: variant.annotations.gnomad_af_oth_female
      },
      south_asian: {
        total: variant.annotations.gnomad_af_sas,
        male: variant.annotations.gnomad_af_sas_male,
        female: variant.annotations.gnomad_af_sas_female
      }
    },
    cadd_scores: {
      raw: variant.annotations.cadd_rawscore,
      phread: variant.annotations.cadd_phred
    },
    nearest_genes: await nearestGenes(variant)
  }
}

export async function variantIDSearch (input: paramsFormatType): Promise<any[]> {
  let variantSchema = humanVariantSchema
  if (input.organism === 'Mus musculus') {
    variantSchema = mouseVariantSchema
  }
  delete input.organism

  let useIndex = ''
  if (input.chr !== undefined && input.position !== undefined) {
    input.region = `${input.chr as string}:${input.position as string}-${parseInt(input.position as string) + 1}`
    useIndex = `OPTIONS { indexHint: "${INDEX_MDI_POS}", forceIndexHint: true }`
    delete input.chr
    delete input.position
  }

  let filterBy = ''
  const filterSts = getFilterStatements(variantSchema, preProcessVariantParams(input))
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  } else {
    return []
  }
  const query = `
    FOR record IN ${variantSchema.db_collection_name as string} ${useIndex}
    ${filterBy}
    SORT record._key
    LIMIT 0, ${QUERY_LIMIT}
    RETURN record._id
  `
  return await (await db.query(query)).all()
}

export async function findVariants (input: paramsFormatType): Promise<any[]> {
  let variantSchema = humanVariantSchema
  if (input.organism === 'Mus musculus') {
    variantSchema = mouseVariantSchema
  }
  delete input.organism
  let useIndex = ''
  if (input.region !== undefined) {
    useIndex = `OPTIONS { indexHint: "${INDEX_MDI_POS}", forceIndexHint: true }`
  }
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  let filterBy = ''
  const filterSts = getFilterStatements(variantSchema, preProcessVariantParams(input))
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }
  const query = `
    FOR record IN ${variantSchema.db_collection_name as string} ${useIndex}
    ${filterBy}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(variantSchema, false, frequenciesDBReturn, ['annotations'])} }
  `
  return await (await db.query(query)).all()
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

  let filterBy = ''
  const filterSts = getFilterStatements(humanVariantSchema, preProcessVariantParams(input))
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }
  const query = `
    FOR record IN ${humanVariantSchema.db_collection_name as string} OPTIONS { indexHint: "${INDEX_MDI_POS}", forceIndexHint: true }
    ${filterBy}
    RETURN [
      record.chr,
      record.pos,
      record.annotations.af_afr,
      record.annotations.af_ami,
      record.annotations.af_amr,
      record.annotations.af_asj,
      record.annotations.af_eas,
      record.annotations.af_fin,
      record.annotations.af_nfe,
      record.annotations.af_sas
    ]
  `

  const header = ['chr', 'pos', 'afr', 'ami', 'amr', 'asj', 'eas', 'fin', 'nfe', 'sas']

  const alleles = await (await db.query(query)).all()

  if (alleles.length !== 0) {
    return [header].concat(alleles)
  }

  return alleles
}

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
