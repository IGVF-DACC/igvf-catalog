import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { preProcessRegionParam, paramsFormatType, getFilterStatements, getDBReturnStatements } from '../_helpers'
import { descriptions } from '../descriptions'

const MAX_PAGE_SIZE = 500

const schema = loadSchemaConfig()
const variantSchema = schema['sequence variant']

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
  'gnomad_af_amr_sas_female',
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
  minimum_maf: z.number().default(0),
  maximum_maf: z.number().default(1),
  page: z.number().default(0)
})

export const variantFormat = z.object({
  _id: z.string(),
  chr: z.string(),
  pos: z.number(),
  rsid: z.array(z.string()).optional(),
  ref: z.string(),
  alt: z.string(),
  spdi: z.string().optional(),
  hgvs: z.string().optional(),
  qual: z.string(),
  filter: z.any(),
  annotations: z.any(),
  source: z.string(),
  source_url: z.string()
})

export const variantSimplifiedFormat = z.object({
  chr: z.string(),
  pos: z.number(),
  ref: z.string(),
  alt: z.string(),
  rsid: z.array(z.string()).optional()
})

function preProcessVariantParams (input: paramsFormatType): paramsFormatType {
  if (input.variant_id !== undefined) {
    input._id = `variants/${input.variant_id}`
    delete input.variant_id
  }

  if (input.GENCODE_category !== undefined) {
    input['annotations.funseq_description'] = input.GENCODE_category
    delete input.GENCODE_category
  }

  if (input.source !== undefined) {
    input[`annotations.${(input.source as string).replace('gnomad_', '')}`] = `range:${input.minimum_maf as string}-${input.maximum_maf as string}`
    delete input.minimum_maf
    delete input.maximum_maf
    delete input.source
  }
  return preProcessRegionParam(input, 'pos')
}

async function conditionalSearch (input: paramsFormatType): Promise<any[]> {
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
    FOR record IN ${variantSchema.db_collection_name} ${useIndex}
    ${filterBy}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(variantSchema, false, frequenciesDBReturn, ['annotations'])} }
  `

  return await (await db.query(query)).all()
}

const variants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants', description: descriptions.variants } })
  .input(variantsQueryFormat.merge(z.object({ limit: z.number().optional() })))
  .output(z.array(variantFormat))
  .query(async ({ input }) => await conditionalSearch(input))

const variantByFrequencySource = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/freq', description: descriptions.variants_by_freq } })
  .input(variantsFreqQueryFormat.omit({ id: true }))
  .output(z.array(variantFormat))
  .query(async ({ input }) => await conditionalSearch(input))

export const variantsRouters = {
  variantByFrequencySource,
  variants
}
