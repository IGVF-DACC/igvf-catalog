import { any, z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { findVariantIDByHgvs, findVariantIDByRSID, findVariantIDBySpdi, findVariantIDsByRegion, variantFormat } from '../nodes/variants'
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
  variant_1_pos: z.number().optional(),
  variant_1_spdi: z.string().optional(),
  variant_1_hgvs: z.string().optional(),
  variant_2_pos: z.number().optional(),
  variant_2_spdi: z.string().optional(),
  variant_2_hgvs: z.string().optional(),
  source: z.string().optional(),
  source_url: z.string().optional(),
  'sequence variant': z.string().or(z.array(variantFormat)).optional()
})

const variantLDQueryFormat = z.object({
  variant_id: z.string().trim().optional(),
  rsid: z.string().trim().optional(),
  spdi: z.string().trim().optional(),
  hgvs: z.string().trim().optional(),
  region: z.string().trim().optional(),
  r2: z.string().trim().optional(),
  d_prime: z.string().trim().optional(),
  ancestry: ancestries.optional(),
  page: z.number().default(0),
  verbose: z.enum(['true', 'false']).default('false')
})

async function addVariantData(lds: any) {
  const lds_variant_ids = new Set<string>()
  lds.forEach((ld: Record<string, string>) => {
    lds_variant_ids.add(ld.variant_1)
    lds_variant_ids.add(ld.variant_2)
  })

  const variant_query = `
    FOR record in variants
    FILTER record._id IN ['${Array.from(lds_variant_ids).join('\',\'')}']
    RETURN {
      id: record._id,
      spdi: record.spdi,
      hgvs: record.hgvs,
      pos: record['pos:long']
    }
  `
  const variant_data = await (await db.query(variant_query)).all()

  const variant_data_map: Record<string, any> = {}
  variant_data.forEach(v_data => {
    variant_data_map[v_data.id] = {
      spdi: v_data.spdi,
      hgvs: v_data.hgvs,
      pos: v_data.pos
    }
  })

  lds.forEach((ld: Record<string, string>) => {
    ld['variant_1_pos'] = variant_data_map[ld.variant_1].pos
    ld['variant_1_spdi'] = variant_data_map[ld.variant_1].spdi
    ld['variant_1_hgvs'] = variant_data_map[ld.variant_1].hgvs
    ld['variant_2_pos'] = variant_data_map[ld.variant_2].pos
    ld['variant_2_spdi'] = variant_data_map[ld.variant_2].spdi
    ld['variant_2_hgvs'] = variant_data_map[ld.variant_2].hgvs
    delete ld.variant_1
    delete ld.variant_2
  })
}

async function findVariantLDs(input: paramsFormatType): Promise<any[]> {
  let variant_id, variant_ids
  if (input.variant_id !== undefined) {
    variant_id = `variants/${decodeURIComponent(input.variant_id as string)}`
  } else if (input.spdi !== undefined) {
    variant_id = await findVariantIDBySpdi(decodeURIComponent(input.spdi as string))
  } else if (input.hgvs !== undefined) {
    variant_id = await findVariantIDByHgvs(decodeURIComponent(input.hgvs as string))
  } else if (input.rsid !== undefined) {
    variant_ids = await findVariantIDByRSID(decodeURIComponent(input.rsid as string))
  }else if (input.region !== undefined) {
    variant_ids = await findVariantIDsByRegion(input.region as string)
  }

  delete input.variant_id
  delete input.spdi
  delete input.hgvs
  delete input.rsid
  delete input.region

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

  let variantCompare = `== '${variant_id}'`
  if (variant_ids !== undefined)
    variantCompare = `IN ['${variant_ids?.join('\',\'')}']`

  const query = `
    FOR record IN ${ldSchemaObj.db_collection_name}
      FILTER (record._from ${variantCompare} OR record._to ${variantCompare}) ${filters}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      LET otherRecordKey = PARSE_IDENTIFIER(record._from ${variantCompare} ? record._to : record._from).key
      RETURN {
        ${getDBReturnStatements(ldSchemaObj)},
        'variant_1': record._from,
        'variant_2': record._to,
        'sequence variant': ${input.verbose === 'true' ? `(${verboseQuery})` : 'otherRecordKey'}
      }
  `
  const lds = await (await db.query(query)).all()

  await addVariantData(lds)

  return lds
}

const variantsFromVariantID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/variant_ld', description: descriptions.variants_variants } })
  .input(variantLDQueryFormat.merge(z.object({ limit: z.number().optional() })))
  .output(z.array(variantsVariantsFormat))
  .query(async ({ input }) => await findVariantLDs(input))

export const variantsVariantsRouters = {
  variantsFromVariantID
}
