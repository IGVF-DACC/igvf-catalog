import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { preProcessRegionParam, paramsFormatType, getFilterStatements, getDBReturnStatements } from '../_helpers'
import { descriptions } from '../descriptions'

const MAX_PAGE_SIZE = 500

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
const frequenciesDBReturn = `'annotations': { ${frequenciesReturn.join(',')}, 'GENCODE_category': record['annotations']['funseq_description'] }`

export const variantsQueryFormat = z.object({
  spdi: z.string().trim().optional(),
  hgvs: z.string().trim().optional(),
  variant_id: z.string().trim().optional(),
  region: z.string().trim().optional(),
  rsid: z.string().trim().optional(),
  GENCODE_category: z.enum(['coding', 'noncoding']).optional(),
  mouse_strain: z.enum(['129S1_SvImJ', 'A_J', 'CAST_EiJ', 'NOD_ShiLtJ', 'NZO_HlLtJ', 'PWK_PhJ', 'WSB_EiJ']).optional(),
  organism: z.enum(['Mus musculus', 'Homo sapiens']).default('Homo sapiens'),
  page: z.number().default(0)
})

const variantsFreqQueryFormat = z.object({
  source: frequencySources,
  spdi: z.string().trim().optional(),
  hgvs: z.string().trim().optional(),
  region: z.string().trim().optional(),
  id: z.string().trim().optional(),
  rsid: z.string().trim().optional(),
  GENCODE_category: z.enum(['coding', 'noncoding']).optional(),
  minimum_af: z.number().default(0),
  maximum_af: z.number().default(1),
  page: z.number().default(0)
})

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
    "bravo_af": z.number().nullish(),
    "gnomad_af_total": z.number().nullish(),
    "gnomad_af_afr": z.number().nullish(),
    "gnomad_af_afr_female": z.number().nullish(),
    "gnomad_af_afr_male": z.number().nullish(),
    "gnomad_af_ami": z.number().nullish(),
    "gnomad_af_ami_female": z.number().nullish(),
    "gnomad_af_ami_male": z.number().nullish(),
    "gnomad_af_amr": z.number().nullish(),
    "gnomad_af_amr_female": z.number().nullish(),
    "gnomad_af_amr_male": z.number().nullish(),
    "gnomad_af_asj": z.number().nullish(),
    "gnomad_af_asj_female": z.number().nullish(),
    "gnomad_af_asj_male": z.number().nullish(),
    "gnomad_af_eas": z.number().nullish(),
    "gnomad_af_eas_female": z.number().nullish(),
    "gnomad_af_eas_male": z.number().nullish(),
    "gnomad_af_female": z.number().nullish(),
    "gnomad_af_fin": z.number().nullish(),
    "gnomad_af_fin_female": z.number().nullish(),
    "gnomad_af_fin_male": z.number().nullish(),
    "gnomad_af_male": z.number().nullish(),
    "gnomad_af_nfe": z.number().nullish(),
    "gnomad_af_nfe_female": z.number().nullish(),
    "gnomad_af_nfe_male": z.number().nullish(),
    "gnomad_af_oth": z.number().nullish(),
    "gnomad_af_oth_female": z.number().nullish(),
    "gnomad_af_oth_male": z.number().nullish(),
    "gnomad_af_sas": z.number().nullish(),
    "gnomad_af_sas_male": z.number().nullish(),
    "gnomad_af_sas_female": z.number().nullish(),
    "gnomad_af_raw": z.number().nullish(),
    "GENCODE_category": z.string().nullish()
  }),
  source: z.string(),
  source_url: z.string(),
  // this is a temporary solution, we will add the organism property for human variants when reloading the collection
  organism: z.string().nullable()
}).transform(({ organism, ...rest }) => ({
  organism: organism ?? 'Homo sapiens',
  ...rest
}))

export const variantSimplifiedFormat = z.object({
  chr: z.string(),
  pos: z.number(),
  ref: z.string(),
  alt: z.string(),
  rsid: z.array(z.string()).optional()
})

export async function findVariantIDBySpdi(spdi: string): Promise<string | null> {
  const query = `
    FOR record in ${humanVariantSchema.db_collection_name}
    FILTER record.spdi == '${spdi}'
    LIMIT 1
    RETURN record._id
  `
  return (await (await db.query(query)).all())[0]
}

export async function findVariantIDByRSID(rsid: string): Promise<string[]> {
  const query = `
    FOR record in ${humanVariantSchema.db_collection_name}
    FILTER '${rsid}' IN record.rsid
    RETURN record._id
  `
  return await (await db.query(query)).all()
}

export async function findVariantIDByHgvs(hgvs: string): Promise<string | null> {
  const query = `
    FOR record in ${humanVariantSchema.db_collection_name}
    FILTER record.hgvs == '${hgvs}'
    LIMIT 1
    RETURN record._id
  `
  return (await (await db.query(query)).all())[0]
}

export async function findVariantIDsByRegion(region: string): Promise<string[]> {
  const query = `
    FOR record in ${humanVariantSchema.db_collection_name} OPTIONS { indexHint: "region", forceIndexHint: true }
    FILTER ${getFilterStatements(humanVariantSchema, preProcessRegionParam({region: region}, 'pos'))}
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

async function variantSearch (input: paramsFormatType): Promise<any[]> {
  let variantSchema = humanVariantSchema
  if (input.organism === 'Mus musculus') {
    variantSchema = mouseVariantSchema
  }
  delete input.organism

  let useIndex = ''
  if (input.region !== undefined) {
    useIndex = 'OPTIONS { indexHint: "region", forceIndexHint: true }'
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

export async function variantIDSearch (input: paramsFormatType): Promise<any[]> {
  let variantSchema = humanVariantSchema
  if (input.organism === 'Mus musculus') {
    variantSchema = mouseVariantSchema
  }
  delete input.organism

  let useIndex = ''
  if (input.chr !== undefined && input.position !== undefined) {
    input.region = `${input.chr}:${input.position}-${input.position}`
    useIndex = 'OPTIONS { indexHint: "region", forceIndexHint: true }'
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

const variants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants', description: descriptions.variants } })
  .input(variantsQueryFormat.merge(z.object({ limit: z.number().optional() })))
  .output(z.array(variantFormat))
  .query(async ({ input }) => await variantSearch(input))

const variantByFrequencySource = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/freq', description: descriptions.variants_by_freq } })
  .input(variantsFreqQueryFormat.omit({ id: true }))
  .output(z.array(variantFormat))
  .query(async ({ input }) => await variantSearch(input))

export const variantsRouters = {
  variantByFrequencySource,
  variants
}
