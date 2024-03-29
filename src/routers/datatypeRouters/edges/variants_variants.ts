import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { variantFormat } from '../nodes/variants'
import { descriptions } from '../descriptions'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'

const MAX_PAGE_SIZE = 500

const schema = loadSchemaConfig()

const ldSchemaObj = schema['topld in linkage disequilibrium with']
const variantsSchemaObj = schema['sequence variant']

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
  variant_id: z.string().trim(),
  r2: z.string().trim().optional(),
  d_prime: z.string().trim().optional(),
  // label: z.enum(['linkage disequilibrum']).optional(), NOTE: we currently have one availble value: 'linkage disequilibrium'
  ancestry: ancestries.optional(),
  page: z.number().default(0),
  verbose: z.enum(['true', 'false']).default('false')
})

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

export const variantsVariantsRouters = {
  variantsFromVariantID
}
