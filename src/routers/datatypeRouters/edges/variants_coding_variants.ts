import { z } from 'zod'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { QUERY_LIMIT } from '../../../constants'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { singleVariantQueryFormat } from '../nodes/variants'

const MAX_PAGE_SIZE = 500

const schema = loadSchemaConfig()

const variantCodingVariantSchema = schema['variants to coding variant']
const variantSchema = schema['sequence variant']
const codingVariantSchema = schema['coding variant']

const codingVariantsQueryFormat = z.object({
  name: z.string().optional(),
  hgvsp: z.string().optional(),
  protein_name: z.string().optional(),
  gene_name: z.string().optional(),
  position: z.string().optional(),
  transcript_id: z.string().optional(),
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
    FOR record IN ${variantCodingVariantSchema.db_collection_name}
    FILTER record._from == 'variants/${variant[0]._id}'
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN
      (
        FOR otherRecord in ${codingVariantSchema.db_collection_name}
        FILTER otherRecord._id == record._to
        RETURN {${getDBReturnStatements(codingVariantSchema).replaceAll('record', 'otherRecord')}}
      )[0]
  `

  return await (await db.query(query)).all()
}

async function findVariants (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filters = getFilterStatements(codingVariantSchema, input)
  if (filters !== undefined || filters !== '') {
    filters = `FILTER ${filters}`
  }

  const query = `
    LET codingVariants = (FOR record IN ${codingVariantSchema.db_collection_name}
      ${filters}
      SORT record.gene_name, record['aapos:long']
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN record._id)

    FOR record in ${variantCodingVariantSchema.db_collection_name}
    FILTER record._to IN codingVariants
    RETURN (
      FOR otherRecord in ${variantSchema.db_collection_name}
      FILTER otherRecord._id == record._from
      RETURN {${getDBReturnStatements(variantSchema, true).replaceAll('record', 'otherRecord')}}
    )[0]
  `

  return await (await db.query(query)).all()
}

const codingVariantsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/coding-variants', description: descriptions.variants_genes } })
  .input(singleVariantQueryFormat.omit({ organism: true }))
  .output(z.any())
  .query(async ({ input }) => await findCodingVariants(input))

const variantsFromCodingVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/coding-variants/variants', description: descriptions.genes_variants } })
  .input(codingVariantsQueryFormat)
  .output(z.any())
  .query(async ({ input }) => await findVariants(input))

export const variantsCodingVariantsRouters = {
  codingVariantsFromVariants,
  variantsFromCodingVariants
}
