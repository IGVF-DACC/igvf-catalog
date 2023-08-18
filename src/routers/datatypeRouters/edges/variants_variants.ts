import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { variantFormat } from '../nodes/variants'

const schema = loadSchemaConfig()

const schemaObj = schema['topld in linkage disequilibrium with']

const routerEdge = new RouterEdges(schemaObj)

const ancestries = z.enum(['AFR', 'EAS', 'EUR', 'SAS'])
const labels = z.enum(['linkage disequilibrum'])

const variantLDQueryFormat = z.object({
  variant_id: z.string(),
  r2: z.string().optional(),
  d_prime: z.string().optional(),
  label: labels.optional(),
  ancestry: ancestries.optional(),
  page: z.number().default(0)
})

const variantsFromVariantID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variant/{variant_id}/variant_ld' } })
  .input(variantLDQueryFormat)
  .output(z.array(variantFormat))
  .query(async ({ input }) => await routerEdge.getBidirectionalByID(input, 'variant_id', input.page, '_key'))

export const variantsVariantsRouters = {
  variantsFromVariantID
}
