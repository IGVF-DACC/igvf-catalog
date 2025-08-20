import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { db } from '../../../database'
import { paramsFormatType, getFilterStatements, getDBReturnStatements } from '../_helpers'
import { descriptions } from '../descriptions'
import { QUERY_LIMIT } from '../../../constants'

const MAX_PAGE_SIZE = 25

const schema = loadSchemaConfig()
const codingVariantSchema = schema['coding variant']

const codingVariantsQueryFormat = z.object({
  id: z.string().optional(),
  name: z.string().optional(),
  hgvsp: z.string().optional(),
  protein_id: z.string().optional(),
  protein_name: z.string().optional(),
  gene_name: z.string().optional(),
  amino_acid_position: z.string().optional(),
  transcript_id: z.string().optional(),
  page: z.number().default(0),
  limit: z.number().optional()
// eslint-disable-next-line @typescript-eslint/naming-convention
}).transform(({ amino_acid_position, name, ...rest }) => ({
  aapos: amino_acid_position,
  name: name?.replaceAll('?', '!').replaceAll('>', '-'),
  ...rest
}))

export const codingVariantsFormat = z.object({
  _id: z.string(),
  name: z.string(),
  ref: z.string().nullable(),
  alt: z.string().nullable(),
  protein_name: z.string().nullable(),
  protein_id: z.string().nullable(),
  gene_name: z.string().nullable(),
  transcript_id: z.string().nullable(),
  aapos: z.number().nullable(),
  hgvsp: z.string().nullable(),
  hgvs: z.string().nullish(),
  refcodon: z.string().nullable(),
  codonpos: z.number().nullable(),
  SIFT_score: z.number().nullable(),
  SIFT4G_score: z.number().nullable(),
  Polyphen2_HDIV_score: z.number().nullable(),
  Polyphen2_HVAR_score: z.number().nullable(),
  VEST4_score: z.number().nullable(),
  Mcap_score: z.number().nullable(),
  REVEL_score: z.number().nullable(),
  MutPred_score: z.number().nullable(),
  BayesDel_addAF_score: z.number().nullable(),
  BayesDel_noAF_score: z.number().nullable(),
  VARITY_R_score: z.number().nullable(),
  VARITY_ER_score: z.number().nullable(),
  VARITY_R_LOO_score: z.number().nullable(),
  VARITY_ER_LOO_score: z.number().nullable(),
  ESM1b_score: z.number().nullable(),
  EVE_score: z.number().nullable(),
  AlphaMissense_score: z.number().nullable(),
  CADD_raw_score: z.number().nullable(),
  source: z.string(),
  source_url: z.string()
}).transform(({ name, ...rest }) => ({
  name: name.replaceAll('!', '?').replaceAll('-', '>'),
  ...rest
}))

async function queryCodingVariants (input: paramsFormatType): Promise<any[]> {
  if (input.id !== undefined) {
    input._key = input.id
    delete input.id
  }

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
      FOR record IN ${codingVariantSchema.db_collection_name as string}
      ${filters}
      SORT record.gene_name
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {${getDBReturnStatements(codingVariantSchema).replace('record[\'name\']', 'record[\'name\'] OR record._key')}}
    `

  const cursor = await db.query(query)
  return await cursor.all()
}

const codingVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/coding-variants', description: descriptions.coding_variants } })
  .input(codingVariantsQueryFormat)
  .output(z.array(codingVariantsFormat))
  .query(async ({ input }) => await queryCodingVariants(input))

export const codingVariantsRouters = {
  codingVariants
}
