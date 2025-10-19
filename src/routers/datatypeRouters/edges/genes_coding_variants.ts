import { z } from 'zod'
import { db } from '../../../database'
import { descriptions } from '../descriptions'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { TRPCError } from '@trpc/server'
import { getDBReturnStatements, paramsFormatType } from '../_helpers'
import { publicProcedure } from '../../../trpc'
import { commonHumanEdgeParamsFormat } from '../params'
import { variantSimplifiedFormat } from '../nodes/variants'

const QUERY_LIMIT = 500

const DATASETS = ['SGE', 'VAMP-seq', 'MutPred2', 'ESM-1v'] as const

const geneQueryFormat = z.object({
  gene_id: z.string()
}).merge(commonHumanEdgeParamsFormat).omit({ organism: true, verbose: true })

const allVariantsQueryFormat = z.object({
  gene_id: z.string(),
  dataset: z.enum(DATASETS),
  page: z.number().default(0),
  limit: z.number().optional()
})

const codingVariantsScoresFormat = z.object({
  variant: z.string().or(variantSimplifiedFormat),
  scores: z.array(z.object({
    source: z.string(),
    score: z.number().nullish()
  }))
})

const schema = loadSchemaConfig()
const codingVariantSchema = schema['coding variant']
const codingVariantToPhenotypeSchema = schema['coding variant to phenotype']
const variantSchema = schema['sequence variant']
const geneSchema = schema.gene

async function findAllCodingVariantsFromGenes (input: paramsFormatType): Promise<any[]> {
  if (input.gene_id === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'gene_id is required'
    })
  }

  if (input.dataset !== undefined && !DATASETS.includes(input.dataset as any)) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: `dataset must be one of ${DATASETS.join(', ')}`
    })
  }

  let scoreQuery = ''
  if (input.dataset === 'SGE') {
    scoreQuery = `
      LET sgeVariantPhenotypeIds = (
        FOR v IN variants_phenotypes_coding_variants
          FILTER v._to IN codingVariantsIds
          LET file_doc = DOCUMENT(v.files_filesets)
          FILTER file_doc.preferred_assay_titles[0] == "SGE"
          RETURN v._from
      )

      FOR p IN variants_phenotypes
        FILTER p._id IN sgeVariantPhenotypeIds
        SORT p.score
        RETURN p.score
    `
  } else if (input.dataset === 'VAMP-seq') {
    scoreQuery = `
      FOR p IN ${codingVariantToPhenotypeSchema.db_collection_name as string}
        FILTER p._from IN codingVariantsIds && p.method == "VAMP-seq"
        SORT p.score
        RETURN p.score
    `
  } else if (input.dataset === 'ESM-1v') {
    scoreQuery = `
      FOR p IN ${codingVariantToPhenotypeSchema.db_collection_name as string}
        FILTER p._from IN codingVariantsIds && p.method == "functional effect prediction on scope of genome-wide using ESM-1v variant scoring workflow v1.0.0"
        SORT p.esm_1v_score
        RETURN p.esm_1v_score
    `
  } else if (input.dataset === 'MutPred2') {
    scoreQuery = `
      FOR p IN ${codingVariantToPhenotypeSchema.db_collection_name as string}
        FILTER p._from IN codingVariantsIds && p.method == "functional effect prediction using MutPred2 v0.0.0.0"
        SORT p.pathogenicity_score
        RETURN p.pathogenicity_score
    `
  }

  const query = `
    LET gene_name = DOCUMENT("${geneSchema.db_collection_name as string}/${input.gene_id as string}").name

    LET codingVariantsIds = (
      FOR record IN ${codingVariantSchema.db_collection_name as string}
      FILTER record.gene_name == gene_name
      RETURN record._id
    )

    ${scoreQuery}
  `

  return await ((await db.query(query)).all())
}

async function cachedFindCodingVariantsFromGenes (input: paramsFormatType): Promise<any> {
  const query = `
    FOR doc IN genes_variants_scores
      FILTER doc._key == "${input.gene_id as string}"
      RETURN SLICE(doc.variant_scores, ${input.page as number * (input.limit as number || 25)}, ${input.limit as number || 25})
  `

  const obj = await ((await db.query(query)).all())

  if (Array.isArray(obj) && obj.length > 0) {
    return obj[0]
  }
  return undefined
}

async function findCodingVariantsFromGenes (input: paramsFormatType): Promise<any[]> {
  let limit = 25
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

  const cachedValues = await cachedFindCodingVariantsFromGenes(input)
  if (cachedValues !== undefined) {
    return cachedValues
  }

  const variantDataVerboseQuery = `
    LET variantIds = UNIQUE(variantMap[*].variantId)

    LET variantData = (
      FOR v IN variants
      FILTER v._id IN variantIds
      RETURN {
        [v._id]: {${getDBReturnStatements(variantSchema, true).replaceAll('record', 'v')}}
      }
    )

    LET variantDict = MERGE(variantData)
  `

  // Score map: pathogenicity_score => MutPred2, esm_1v_score => ESM1, score => VampSeq
  const query = `
    LET gene_name = DOCUMENT("${geneSchema.db_collection_name as string}/${input.gene_id as string}").name

    LET codingVariants = (
      FOR cv IN ${codingVariantSchema.db_collection_name as string}
        FILTER cv.gene_name == gene_name
        RETURN cv._id
    )

    LET variantMap = (
      FOR vcv IN variants_coding_variants
        FILTER vcv._to IN codingVariants
        RETURN { codingVariant: vcv._to, variantId: vcv._from }
    )

    ${input.verbose === 'true' ? variantDataVerboseQuery : ''}

    LET variantLookup = (
      FOR map IN variantMap
        RETURN { [map.codingVariant]: ${input.verbose === 'true' ? 'variantDict[map.variantId]' : 'SPLIT(map.variantId, "/")[1]'} }
    )

    LET variantByCodingVariant = MERGE(variantLookup)

    LET sgeResults = (
      FOR v IN variants_phenotypes_coding_variants
        FILTER v._to IN codingVariants
        LET phenotype = DOCUMENT(v._from)
        LET fileset = DOCUMENT(v.files_filesets)
        RETURN {
          variant: variantByCodingVariant[v._to],
          score: phenotype.score,
          source: fileset.preferred_assay_titles[0]
        }
    )

    LET otherResults = (
      FOR p IN ${codingVariantToPhenotypeSchema.db_collection_name as string}
        FILTER p._from IN codingVariants
        RETURN {
          variant: variantByCodingVariant[p._from],
          score: p.pathogenicity_score OR p.esm_1v_score OR p.score,
          source: p.method
        }
    )

    FOR doc IN UNION(sgeResults, otherResults)
      COLLECT variant = doc.variant INTO grouped = doc
      LET maxScore = MAX(grouped[*].score)
      SORT maxScore DESC
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        variant,
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

const allCodingVariantsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/coding-variants/all-scores', description: descriptions.genes_coding_variants } })
  .input(allVariantsQueryFormat)
  .output(z.array(z.number().optional()))
  .query(async ({ input }) => await findAllCodingVariantsFromGenes(input))

export const genesCodingVariantsRouters = {
  codingVariantsFromGenes,
  allCodingVariantsFromGenes
}
