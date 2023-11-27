import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { preProcessRegionParam, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

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
  variant_id: z.string().optional(),
  spdi: z.string().trim().optional(),
  hgvs: z.string().trim().optional(),
  region: z.string().optional(),
  rsid: z.string().optional(),
  funseq_description: z.string().optional(),
  page: z.number().default(0)
})

const variantsFreqQueryFormat = z.object({
  source: frequencySources,
  region: z.string().optional(),
  id: z.string().optional(),
  rsid: z.string().optional(),
  spdi: z.string().trim().optional(),
  hgvs: z.string().trim().optional(),
  funseq_description: z.string().optional(),
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

function preProcessVariantParams (input: paramsFormatType): paramsFormatType {
  if (input.variant_id !== undefined) {
    input._id = `variants/${input.variant_id}`
    delete input.variant_id
  }

  if (input.funseq_description !== undefined) {
    input['annotations.funseq_description'] = input.funseq_description
    delete input.funseq_description
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
  let queryOptions = ''
  if (input.region !== undefined) {
    queryOptions = 'OPTIONS { indexHint: "region", forceIndexHint: true }'
  }

  return await router.getObjects(preProcessVariantParams(input), queryOptions)
}

const schemaObj = schema['sequence variant']
const router = new RouterFilterBy(schemaObj)

const variants = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: descriptions.variants } })
  .input(variantsQueryFormat)
  .output(z.array(variantFormat))
  .query(async ({ input }) => await conditionalSearch(input))

const variantByFrequencySource = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}/freq`, description: descriptions.variants_by_freq } })
  .input(variantsFreqQueryFormat.omit({ id: true }))
  .output(z.array(variantFormat))
  .query(async ({ input }) => await conditionalSearch(input))

export const variantsRouters = {
  variantByFrequencySource,
  variants
}
