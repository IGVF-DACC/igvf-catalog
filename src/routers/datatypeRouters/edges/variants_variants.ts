import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { variantFormat } from '../nodes/variants'

const schema = loadSchemaConfig()

const schemaObj = schema['topld in linkage disequilibrium with']

const routerEdge = new RouterEdges(schemaObj)

const ancestries = z.enum(['AFR', 'EAS', 'EUR', 'SAS'])

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
  source: z.string().optional(),
  source_url: z.string().optional(),
  'sequence variant': z.string().or(z.array(variantFormat)).optional()
})

const variantLDQueryFormat = z.object({
  variant_id: z.string(),
  r2: z.string().optional(),
  d_prime: z.string().optional(),
  // label: z.enum(['linkage disequilibrum']).optional(), NOTE: we currently have one availble value: 'linkage disequilibrium'
  ancestry: ancestries.optional(),
  page: z.number().default(0),
  verbose: z.enum(['true', 'false']).default('false')
})

const variantsFromVariantID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/{variant_id}/variant_ld' } })
  .input(variantLDQueryFormat)
  .output(z.array(variantsVariantsFormat))
  .query(async ({ input }) => await routerEdge.getBidirectionalByID(input, 'variant_id', input.page, '_key', input.verbose === 'true'))

export const variantsVariantsRouters = {
  variantsFromVariantID
}
