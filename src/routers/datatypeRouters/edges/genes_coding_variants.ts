import { z } from 'zod'
import { db } from '../../../database'
import { descriptions } from '../descriptions'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { genesCommonQueryFormat, commonHumanEdgeParamsFormat } from '../params'
import { geneSearch } from '../nodes/genes'
import { TRPCError } from '@trpc/server'
import { paramsFormatType } from '../_helpers'
import { publicProcedure } from '../../../trpc'

const MAX_PAGE_SIZE = 100

const codingVariantsScoresFormat = z.object({
  coding_variant_id: z.string(),
  scores: z.object({
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
    CADD_raw_score: z.number().nullable()
  })
})

const schema = loadSchemaConfig()
const codingVariantSchema = schema['coding variant']

async function findCodingVariantsFromGenes (input: paramsFormatType): Promise<any[]> {
  let limit = MAX_PAGE_SIZE
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { gene_id, hgnc, gene_name: name, alias, organism } = input
  const geneInput: paramsFormatType = { gene_id, hgnc, name, alias, organism, page: 0 }
  delete input.hgnc
  delete input.gene_name
  delete input.alias
  delete input.organism
  const genes = await geneSearch(geneInput)
  const geneNames = genes.map(gene => `${gene.name as string}`)

  if (geneNames.length === 0) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Gene not found.'
    })
  }

  const query = `
    FOR record IN ${codingVariantSchema.db_collection_name as string}
    FILTER record.gene_name IN ['${geneNames.join(',')}']
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN {
      coding_variant_id: record._key,
      scores: {
        SIFT_score: record.SIFT_score,
        SIFT4G_score: record.SIFT4G_score,
        Polyphen2_HDIV_score: record.Polyphen2_HDIV_score,
        Polyphen2_HVAR_score: record.Polyphen2_HVAR_score,
        VEST4_score: record.VEST4_score,
        REVEL_score: record.REVEL_score,
        MutPred_score: record.MutPred_score,
        BayesDel_addAF_score: record.BayesDel_addAF_score,
        BayesDel_noAF_score: record.BayesDel_noAF_score,
        VARITY_R_score: record.VARITY_R_score,
        VARITY_ER_score: record.VARITY_ER_score,
        VARITY_R_LOO_score: record.VARITY_R_LOO_score,
        VARITY_ER_LOO_score: record.VARITY_ER_LOO_score,
        ESM1b_score: record.ESM1b_score,
        AlphaMissense_score: record.AlphaMissense_score,
        CADD_raw_score: record.CADD_raw_score
      }
    }
  `

  return await ((await db.query(query)).all())
}

const codingVariantsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/coding-variants', description: descriptions.genes_coding_variants } })
  .input(genesCommonQueryFormat.merge(commonHumanEdgeParamsFormat).omit({ verbose: true, organism: true }))
  .output(z.array(codingVariantsScoresFormat))
  .query(async ({ input }) => await findCodingVariantsFromGenes(input))

export const genesCodingVariantsRouters = {
  codingVariantsFromGenes
}
