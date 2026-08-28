import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { db } from '../../../database'
import { paramsFormatType, getFilterStatements, getDBReturnStatements } from '../_helpers'
import { descriptions } from '../descriptions'
import { QUERY_LIMIT } from '../../../constants'
import { getSchema } from '../schema'
import { TRPCError } from '@trpc/server'

const MAX_PAGE_SIZE = 25

const codingVariantSchema = getSchema('data/schemas/nodes/coding_variants.DbNSFP.json')
const codingVariantCollectionName = codingVariantSchema.db_collection_name as string

export const ALT_AMINO_ACID_CODES = [
  'A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L',
  'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y',
  '*'
] as const

export const CODING_VARIANT_FILTER_FIELDS = [
  '_key', 'name', 'hgvsp', 'protein_id', 'protein_name', 'gene_name', 'aapos', 'alt', 'transcript_id'
] as const

const codingVariantsQueryFormat = z.object({
  id: z.string().optional(),
  name: z.string().optional(),
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
}).transform(({ amino_acid_position, alt_amino_acid, name, uniprot_name, ...rest }) => ({
  ...rest,
  ...(amino_acid_position !== undefined ? { aapos: amino_acid_position } : {}),
  ...(alt_amino_acid !== undefined ? { alt: alt_amino_acid } : {}),
  ...(uniprot_name !== undefined ? { protein_name: uniprot_name } : {}),
  ...(name !== undefined ? { name: name.replaceAll('?', '!').replaceAll('>', '-') } : {})
}))

export function pickCodingVariantFilters (input: paramsFormatType): paramsFormatType {
  return Object.fromEntries(
    CODING_VARIANT_FILTER_FIELDS
      .filter((key) => input[key] !== undefined)
      .map((key) => [key, input[key]])
  )
}

export function validateCodingVariantAapos (input: paramsFormatType): void {
  if (input.aapos !== undefined && isNaN(Number(input.aapos))) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Invalid amino_acid_position. It should be a number.'
    })
  }
}

function validateCodingVariantsQueryInput (input: paramsFormatType): void {
  if (
    input._key === undefined &&
    input.name === undefined &&
    input.hgvsp === undefined &&
    input.protein_id === undefined &&
    input.protein_name === undefined &&
    input.gene_name === undefined &&
    input.transcript_id === undefined
  ) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one coding variant parameter must be defined: id, name, hgvsp, protein_id, uniprot_name, gene_name, or transcript_id.'
    })
  }
}

export const codingVariantsFormat = z.object({
  _id: z.string(),
  name: z.string().nullable(),
  ref: z.string().nullable(),
  alt: z.string().nullable(),
  protein_name: z.string().nullable(),
  protein_id: z.string().nullable(),
  gene_name: z.string().nullable(),
  transcript_id: z.string().nullable(),
  aapos: z.number().nullable(),
  hgvsp: z.string().nullable(),
  hgvsc: z.string().nullish(),
  refcodon: z.string().nullable(),
  codonpos: z.number().nullable(),
  SIFT_score: z.number().nullable(),
  SIFT4G_score: z.number().nullable(),
  Polyphen2_HDIV_score: z.number().nullable(),
  Polyphen2_HVAR_score: z.number().nullable(),
  VEST4_score: z.number().nullable(),
  REVEL_score: z.number().nullable(),
  MutPred_score: z.number().nullable(),
  BayesDel_addAF_score: z.number().nullable(),
  BayesDel_noAF_score: z.number().nullable(),
  VARITY_R_score: z.number().nullable(),
  VARITY_ER_score: z.number().nullable(),
  VARITY_R_LOO_score: z.number().nullable(),
  VARITY_ER_LOO_score: z.number().nullable(),
  ESM1b_score: z.number().nullable(),
  AlphaMissense_score: z.number().nullable(),
  CADD_raw_score: z.number().nullable(),
  source: z.string(),
  source_url: z.string()
}).transform(({ name, ...rest }) => ({
  name: (name === null) ? null : name.replaceAll('!', '?').replaceAll('-', '>'),
  ...rest
}))

async function queryCodingVariants (input: paramsFormatType): Promise<any[]> {
  validateCodingVariantAapos(input)

  if (input.id !== undefined) {
    input._key = input.id
    delete input.id
  }

  validateCodingVariantsQueryInput(input)

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filters = getFilterStatements(codingVariantSchema, pickCodingVariantFilters(input))
  if (filters !== undefined || filters !== '') {
    filters = `FILTER ${filters}`
  }

  const query = `
      FOR record IN ${codingVariantCollectionName}
      ${filters}
      SORT record.gene_name
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {${getDBReturnStatements(codingVariantSchema).replace('record[\'name\']', 'record[\'name\'] OR record._key')}}
    `
  const cursor = await db.query(query)
  return await cursor.all()
}

const codingVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/coding-variants', description: descriptions.coding_variants, tags: ['Nodes'] } })
  .input(codingVariantsQueryFormat)
  .output(z.array(codingVariantsFormat))
  .query(async ({ input }) => await queryCodingVariants(input))

export const codingVariantsRouters = {
  codingVariants
}
