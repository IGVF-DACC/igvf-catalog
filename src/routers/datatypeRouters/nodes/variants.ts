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
  'dbgap_popfreq',
  'topmed',
  'twinsuk',
  'gnomad',
  'gonl',
  'alspac',
  'korean',
  'estonian',
  'qatari',
  '1000genomes',
  'sgdp_prj',
  'vietnamese',
  'tommo',
  'genome_dk',
  'siberian',
  'northernsweden',
  'korea1k',
  'hapmap',
  'mgp',
  'gnomad_exomes',
  'exac',
  'goesp',
  'chileans',
  'prjeb37584',
  'prjeb36033',
  'hgdp_stanford',
  'page_study',
  'finrisk'
])

export const variantsQueryFormat = z.object({
  spdi: z.string().trim().optional(),
  hgvs: z.string().trim().optional(),
  variant_id: z.string().trim().optional(),
  region: z.string().trim().optional(),
  rsid: z.string().trim().optional(),
  funseq_description: z.string().trim().optional(),
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
  funseq_description: z.string().trim().optional(),
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
  strain: z.string().nullish(),
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
    input._key = input.variant_id
    delete input.variant_id
  }

  if (input.funseq_description !== undefined) {
    input['annotations.funseq_description'] = input.funseq_description
    delete input.funseq_description
  }

  if (input.mouse_strain !== undefined) {
    input.strain = input.mouse_strain
    delete input.mouse_strain
  }

  if (input.source !== undefined) {
    input[`annotations.freq.${input.source}.alt`] = `range:${input.minimum_maf as string}-${input.maximum_maf as string}`
    delete input.minimum_maf
    delete input.maximum_maf
    delete input.source
  }
  return preProcessRegionParam(input, 'pos')
}

async function conditionalSearch (input: paramsFormatType): Promise<any[]> {
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
    RETURN { ${getDBReturnStatements(variantSchema)} }
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
