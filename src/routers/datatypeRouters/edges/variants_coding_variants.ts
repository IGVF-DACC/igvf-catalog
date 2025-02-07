import { z } from 'zod'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { QUERY_LIMIT } from '../../../constants'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { findVariants, singleVariantQueryFormat, variantSimplifiedFormat } from '../nodes/variants'
import { codingVariantsFormat } from '../nodes/coding_variants'

const MAX_PAGE_SIZE = 500

const schema = loadSchemaConfig()

const variantCodingVariantSchema = schema['variants to coding variant']
const variantSchema = schema['sequence variant']
const codingVariantSchema = schema['coding variant']

const codingVariantsQueryFormat = z.object({
  coding_variant_name: z.string().optional(),
  hgvsp: z.string().optional(),
  page: z.number().default(0),
  limit: z.number().optional()
})

function validateInput (input: paramsFormatType): void {
  if (input.spdi === undefined && input.hgvs === undefined && input.variant_id === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one parameter must be defined.'
    })
  }
}

async function findCodingVariants (input: paramsFormatType): Promise<any[]> {
  validateInput(input)

  input.page = 0
  const variant = (await findVariants(input))
  if (variant.length === 0) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Variant not found.'
    })
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const query = `
    FOR record IN ${variantCodingVariantSchema.db_collection_name as string}
    FILTER record._from == 'variants/${variant[0]._id as string}'
    SORT record._key
    LIMIT ${input.page * limit}, ${limit}
    RETURN
      (
        FOR otherRecord in ${codingVariantSchema.db_collection_name as string}
        FILTER otherRecord._id == record._to
        RETURN {${getDBReturnStatements(codingVariantSchema).replaceAll('record', 'otherRecord')}}
      )[0]
  `

  return await (await db.query(query)).all()
}

async function findVariantsFromCodingVariants (input: paramsFormatType): Promise<any[]> {
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

  let filters = getFilterStatements(codingVariantSchema, input)
  if (filters !== undefined || filters !== '') {
    filters = `FILTER ${filters}`
  }

  const query = `
    LET codingVariants = (FOR record IN ${codingVariantSchema.db_collection_name as string}
      ${filters}
      SORT record.gene_name, record.aapos
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN record._id)

    FOR record in ${variantCodingVariantSchema.db_collection_name as string}
    FILTER record._to IN codingVariants
    RETURN (
      FOR otherRecord in ${variantSchema.db_collection_name as string}
      FILTER otherRecord._id == record._from
      RETURN {${getDBReturnStatements(variantSchema, true).replaceAll('record', 'otherRecord')}}
    )[0]
  `

  return await (await db.query(query)).all()
}

const codingVariantsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/coding-variants', description: descriptions.variants_coding_variants } })
  .input(singleVariantQueryFormat.omit({ organism: true }))
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
