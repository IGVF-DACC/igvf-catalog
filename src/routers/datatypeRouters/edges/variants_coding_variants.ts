import { z } from 'zod'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { QUERY_LIMIT } from '../../../constants'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { singleVariantQueryFormat, variantIDSearch, variantSimplifiedFormat } from '../nodes/variants'
import {
  codingVariantsFormat,
  pickCodingVariantFilters,
  validateCodingVariantAapos,
  ALT_AMINO_ACID_CODES
} from '../nodes/coding_variants'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 500

const variantCodingVariantCollectionName = 'variants_coding_variants'
const variantSchema = getSchema('data/schemas/nodes/variants.Favor.json')
const codingVariantSchema = getSchema('data/schemas/nodes/coding_variants.DbNSFP.json')
const codingVariantCollectionName = codingVariantSchema.db_collection_name as string

const variantsFromCodingVariantsQueryFormat = z.object({
  coding_variant_name: z.string().optional(),
  hgvsp: z.string().optional(),
  protein_id: z.string().optional(),
  uniprot_name: z.string().optional(),
  gene_name: z.string().optional(),
  amino_acid_position: z.string().optional(),
  alt_amino_acid: z.enum(ALT_AMINO_ACID_CODES).optional(),
  transcript_id: z.string().optional(),
  page: z.number().default(0),
  limit: z.number().optional()
// eslint-disable-next-line @typescript-eslint/naming-convention
}).transform(({ amino_acid_position, alt_amino_acid, coding_variant_name, uniprot_name, ...rest }) => ({
  ...rest,
  ...(amino_acid_position !== undefined ? { aapos: amino_acid_position } : {}),
  ...(alt_amino_acid !== undefined ? { alt: alt_amino_acid } : {}),
  ...(uniprot_name !== undefined ? { protein_name: uniprot_name } : {}),
  ...(coding_variant_name !== undefined ? { name: coding_variant_name.replaceAll('?', '!').replaceAll('>', '-') } : {})
}))

function validateVariantInput (input: paramsFormatType): void {
  if (input.spdi === undefined && input.hgvs === undefined && input.variant_id === undefined && input.ca_id === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one variant parameter must be defined.'
    })
  }
}

function validateVariantsFromCodingVariantsInput (input: paramsFormatType): void {
  if (
    input.name === undefined &&
    input.hgvsp === undefined &&
    input.protein_id === undefined &&
    input.protein_name === undefined &&
    input.gene_name === undefined &&
    input.transcript_id === undefined
  ) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one coding variant parameter must be defined: coding_variant_name, hgvsp, protein_id, uniprot_name, gene_name, or transcript_id.'
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
  validateVariantsFromCodingVariantsInput(input)
  validateCodingVariantAapos(input)

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const codingVariantInput = pickCodingVariantFilters(input)
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
    LET otherRecord = DOCUMENT(record._from)
    FILTER otherRecord != null
    COLLECT variant = otherRecord
    SORT variant._key
    LIMIT ${input.page as number * limit}, ${limit}

    RETURN {${getDBReturnStatements(variantSchema, true).replaceAll('record', 'variant')}}
`
  return await (await db.query(query)).all()
}

const codingVariantsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/coding-variants', description: descriptions.variants_coding_variants, tags: ['Biological Context Data'] } })
  .input(singleVariantQueryFormat.omit({ organism: true }).merge(z.object({ page: z.number().default(0), limit: z.number().optional() })))
  .output(z.array(codingVariantsFormat))
  .query(async ({ input }) => await findCodingVariants(input))

const variantsFromCodingVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/coding-variants/variants', description: descriptions.coding_variants_variants, tags: ['Biological Context Data'] } })
  .input(variantsFromCodingVariantsQueryFormat)
  .output(z.array(variantSimplifiedFormat.merge(z.object({ _id: z.string() }))))
  .query(async ({ input }) => await findVariantsFromCodingVariants(input))

export const variantsCodingVariantsRouters = {
  codingVariantsFromVariants,
  variantsFromCodingVariants
}
