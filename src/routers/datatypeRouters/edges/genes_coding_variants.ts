import { z } from 'zod'
import { db } from '../../../database'
import { descriptions } from '../descriptions'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { TRPCError } from '@trpc/server'
import { paramsFormatType } from '../_helpers'
import { publicProcedure } from '../../../trpc'

const QUERY_LIMIT = 500

const geneQueryFormat = z.object({
  gene_id: z.string().optional(),
  page: z.number().default(0),
  limit: z.number().optional()
})

const codingVariantsScoresFormat = z.object({
  coding_variant_id: z.string(),
  scores: z.array(z.object({
    source: z.string(),
    score: z.number().optional()
  }))
})

const schema = loadSchemaConfig()
const codingVariantSchema = schema['coding variant']
const codingVariantToPhenotypeSchema = schema['coding variant to phenotype']
const geneSchema = schema.gene

async function findCodingVariantsFromGenes (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= QUERY_LIMIT) ? input.limit as number : QUERY_LIMIT
    delete input.limit
  }

  if (input.gene_id === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'gene_id is required'
    })
  }

  const query = `
    LET gene_name = DOCUMENT("${geneSchema.db_collection_name as string}/${input.gene_id as string}").name

    LET codingVariants = (
      FOR record IN ${codingVariantSchema.db_collection_name as string}
      FILTER record.gene_name == gene_name
      RETURN record._id
    )

    FOR doc IN UNION(
      // SGE
      FOR v IN variants_phenotypes_coding_variants
        FILTER v._to IN codingVariants
        LET files_filesets = DOCUMENT(v.files_filesets)
        LET vPhenotype = DOCUMENT(v._from)
        RETURN {
          coding_variant_id: PARSE_IDENTIFIER(v._to).key,
          score: vPhenotype.score,
          source: files_filesets.preferred_assay_titles[0]
        },

      // VampSeq
      FOR p IN ${codingVariantToPhenotypeSchema.db_collection_name as string}
        FILTER p._from IN codingVariants
        RETURN {
          coding_variant_id: PARSE_IDENTIFIER(p._from).key,
          score: p.abundance_score,
          source: p.source
        }
    )
      COLLECT coding_variant_id = doc.coding_variant_id INTO grouped = doc
      LET maxScore = MAX(grouped[*].score)
      SORT maxScore DESC
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        coding_variant_id,
        scores: grouped[* RETURN { source: CURRENT.source, score: CURRENT.score }]
      }
  `

  return await ((await db.query(query)).all())
}

const codingVariantsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/coding-variants/scores', description: descriptions.genes_coding_variants } })
  .input(geneQueryFormat)
  .output(z.array(codingVariantsScoresFormat))
  .query(async ({ input }) => await findCodingVariantsFromGenes(input))

export const genesCodingVariantsRouters = {
  codingVariantsFromGenes
}
