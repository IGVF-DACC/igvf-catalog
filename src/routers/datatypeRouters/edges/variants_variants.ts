import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { findVariants, singleVariantQueryFormat, variantFormat } from '../nodes/variants'
import { descriptions } from '../descriptions'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { TRPCError } from '@trpc/server'
import { findPredictionsFromVariantCount } from './variants_regulatory_regions'

const MAX_PAGE_SIZE = 500

const schema = loadSchemaConfig()

const ldSchemaObj = schema['topld in linkage disequilibrium with']
const variantsSchemaObj = schema['sequence variant']

const ancestries = z.enum(['AFR', 'EAS', 'EUR', 'SAS'])

const variantsVariantsSummaryFormat = z.object({
  ancestry: z.string(),
  d_prime: z.number().nullish(),
  r2: z.number().nullish(),
  variant_id: z.string(),
  predictions: z.object({
    cell_types: z.array(z.string()),
    genes: z.array(z.object({
      gene_name: z.string(),
      id: z.string()
    }))
  })
})

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
  variant_id: z.string().trim(),
  r2: z.string().trim().optional(),
  d_prime: z.string().trim().optional(),
  // label: z.enum(['linkage disequilibrum']).optional(), NOTE: we currently have one availble value: 'linkage disequilibrium'
  ancestry: ancestries.optional(),
  page: z.number().default(0),
  verbose: z.enum(['true', 'false']).default('false')
})

export async function findVariantLDSummary(input: paramsFormatType): Promise<any[]> {
  const originalPage = input.page as number

  let limit = 15
  if (input.limit !== undefined) {
    limit = (input.limit as number <= 50) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  input.page = 0
  const variant = (await findVariants(input))

  if (variant.length === 0) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Variant not found.'
    })
  }

  const id = `variants/${variant[0]._id}`

  const query = `
  FOR record IN ${ldSchemaObj.db_collection_name}
    FILTER (record._from == '${id}' OR record._to == '${id}')
    LET otherRecordKey = PARSE_IDENTIFIER(record._from == '${id}' ? record._to : record._from).key
    SORT record._key
    LIMIT ${originalPage * limit}, ${limit}
    RETURN {
      'ancestry': record['ancestry'], 'd_prime': record['d_prime:long'],
      'r2': record['r2:long'],
      'variant_id': otherRecordKey
    }
  `

  const objs =  await (await db.query(query)).all()

  for (let i = 0; i < objs.length; i++) {
    const element = objs[i]
    element.predictions = (await findPredictionsFromVariantCount({variant_id: element.variant_id, organism: 'Homo sapiens'}, false))[0]
  }

  return objs
}

async function findVariantLDs(input: paramsFormatType): Promise<any[]> {
  const id = `variants/${decodeURIComponent(input.variant_id as string)}`
  delete input.variant_id

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filters = getFilterStatements(ldSchemaObj, input)
  if (filters) {
    filters = ` AND ${filters}`
  }

  const verboseQuery = `
    FOR otherRecord in ${variantsSchemaObj.db_collection_name}
    FILTER otherRecord._key == otherRecordKey
    RETURN {${getDBReturnStatements(variantsSchemaObj).replaceAll('record', 'otherRecord')}}
  `

  const query = `
    FOR record IN ${ldSchemaObj.db_collection_name}
      FILTER (record._from == '${id}' OR record._to == '${id}') ${filters}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      LET otherRecordKey = PARSE_IDENTIFIER(record._from == '${id}' ? record._to : record._from).key
      RETURN {
        ${getDBReturnStatements(ldSchemaObj)},
        'sequence variant': ${input.verbose === 'true' ? `(${verboseQuery})` : 'otherRecordKey'}
      }
  `

  return await (await db.query(query)).all()
}

const variantsFromVariantID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/variant_ld', description: descriptions.variants_variants } })
  .input(variantLDQueryFormat.merge(z.object({ limit: z.number().optional() })))
  .output(z.array(variantsVariantsFormat))
  .query(async ({ input }) => await findVariantLDs(input))

const variantsFromVariantIDSummary = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/variant_ld/summary', description: descriptions.variants_variants_summary } })
  .input(singleVariantQueryFormat.merge(z.object({ limit: z.number().optional() })))
  .output(z.array(variantsVariantsSummaryFormat))
  .query(async ({ input }) => await findVariantLDSummary(input))

export const variantsVariantsRouters = {
  variantsFromVariantIDSummary,
  variantsFromVariantID
}
