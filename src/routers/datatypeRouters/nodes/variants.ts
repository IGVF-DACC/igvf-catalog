import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'
import { preProcessRegionParam, paramsFormatType } from '../_helpers'

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

const variantsQueryFormat = z.object({
  region: z.string().optional(),
  rsid: z.string().optional(),
  funseq_description: z.string().optional(),
  page: z.number().default(0)
})

const variantsFreqQueryFormat = z.object({
  source: frequencySources,
  region: z.string(),
  funseq_description: z.string().optional(),
  min_alt_freq: z.number().default(0),
  max_alt_freq: z.number().default(1),
  page: z.number().default(0)
})

const variantFormat = z.object({
  _id: z.string(),
  chr: z.string(),
  pos: z.number(),
  rsid: z.array(z.string()).optional(),
  ref: z.string(),
  alt: z.string(),
  qual: z.string(),
  filter: z.any(),
  annotations: z.any(),
  source: z.string(),
  source_url: z.string()
})

function preProcessVariantParams (input: paramsFormatType): paramsFormatType {
  if (input.funseq_description !== undefined) {
    input['annotations.funseq_description'] = input.funseq_description
    delete input.funseq_description
  }

  if (input.source !== undefined) {
    input[`annotations.freq.${input.source}.alt`] = `range:${input.min_alt_freq as string}-${input.max_alt_freq as string}`
    delete input.min_alt_freq
    delete input.max_alt_freq
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
const routerID = new RouterFilterByID(schemaObj)

const variants = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: router.apiSpecs.description } })
  .input(variantsQueryFormat)
  .output(z.array(variantFormat))
  .query(async ({ input }) => await conditionalSearch(input))

export const variantID = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${routerID.path}` } })
  .input(z.object({ id: z.string() }))
  .output(variantFormat)
  .query(async ({ input }) => await routerID.getObjectById(input.id))

const variantByFrequencySource = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}/freq/{source}` } })
  .input(variantsFreqQueryFormat)
  .output(z.array(variantFormat))
  .query(async ({ input }) => await router.getObjects(preProcessVariantParams(input)))

export const variantsRouters = {
  variants,
  variantID,
  variantByFrequencySource
}
