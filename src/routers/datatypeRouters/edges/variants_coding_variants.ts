import { z } from 'zod'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { QUERY_LIMIT } from '../../../constants'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { singleVariantQueryFormat, variantIDSearch, variantSimplifiedFormat } from '../nodes/variants'
import { codingVariantsFormat } from '../nodes/coding_variants'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 500

const variantCodingVariantCollectionName = 'variants_coding_variants'
const variantSchema = getSchema('data/schemas/nodes/variants.Favor.json')
const codingVariantSchema = getSchema('data/schemas/nodes/coding_variants.DbNSFP.json')
const codingVariantCollectionName = codingVariantSchema.db_collection_name as string

const codingVariantsQueryFormat = z.object({
  coding_variant_name: z.string().optional(),
  hgvsp: z.string().optional(),
  page: z.number().default(0),
  limit: z.number().optional()
})

function validateVariantInput (input: paramsFormatType): void {
  if (input.spdi === undefined && input.hgvs === undefined && input.variant_id === undefined && input.ca_id === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one variantparameter must be defined.'
    })
  }
}

function validateCodingVariantInput (input: paramsFormatType): void {
  if (input.coding_variant_name === undefined && input.hgvsp === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one coding variant parameter must be defined.'
    })
  }
}
async function findCodingVariants (input: paramsFormatType): Promise<any[]> {
  validateVariantInput(input)
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const variantInput: paramsFormatType = (({ variant_id, spdi, hgvs, ca_id }) => ({ variant_id, spdi, hgvs, ca_id }))(input)
  delete input.variant_id
  delete input.spdi
  delete input.hgvs
  delete input.ca_id
  const variantIDs = await variantIDSearch(variantInput)

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const query = `
  FOR record IN ${variantCodingVariantCollectionName}
    FILTER record._from IN @variantIDs

    FOR otherRecord IN ${codingVariantCollectionName}
      FILTER otherRecord._id == record._to

      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}

      RETURN {${getDBReturnStatements(codingVariantSchema).replaceAll('record', 'otherRecord')}}
`
  return await (await db.query(query, { variantIDs })).all()
}

async function findVariantsFromCodingVariants (input: paramsFormatType): Promise<any[]> {
  validateCodingVariantInput(input)
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  if (input.coding_variant_name !== undefined) {
    // replace ">" with "-" in coding_variant_name
    input.name = (input.coding_variant_name as string).replace('>', '-')
    delete input.coding_variant_name
  }
  const codingVariantInput: paramsFormatType = (({ name, hgvsp }) => ({ name, hgvsp }))(input)
  delete input.name
  delete input.hgvsp
  const filters = getFilterStatements(codingVariantSchema, codingVariantInput)
  const query = `
  LET codingVariants = (
    FOR record IN ${codingVariantCollectionName}
      FILTER ${filters}
      SORT record.gene_name, record.aapos
      RETURN record._id
  )

  FOR record IN ${variantCodingVariantCollectionName}
    FILTER record._to IN codingVariants
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}

    LET otherRecord = DOCUMENT(record._from)
    FILTER otherRecord != null

    RETURN {${getDBReturnStatements(variantSchema, true).replaceAll('record', 'otherRecord')}}
`
  return await (await db.query(query)).all()
}

const codingVariantsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/coding-variants', description: descriptions.variants_coding_variants } })
  .input(singleVariantQueryFormat.omit({ organism: true }).merge(z.object({ page: z.number().default(0), limit: z.number().optional() })))
  .output(z.array(codingVariantsFormat))
  .query(async ({ input }) => await findCodingVariants(input))

const variantsFromCodingVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/coding-variants/variants', description: descriptions.coding_variants_variants } })
  .input(codingVariantsQueryFormat)
  .output(z.array(variantSimplifiedFormat.merge(z.object({ _id: z.string() }))))
  .query(async ({ input }) => await findVariantsFromCodingVariants(input))

export const variantsCodingVariantsRouters = {
  codingVariantsFromVariants,
  variantsFromCodingVariants
}
