import { z } from 'zod'
import { db } from '../../../database'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { getDBReturnStatements, paramsFormatType } from '../_helpers'
import { publicProcedure } from '../../../trpc'
import { commonHumanEdgeParamsFormat, genesCommonQueryFormat } from '../params'
import { variantSimplifiedFormat } from '../nodes/variants'
import { getSchema } from '../schema'
import { geneSearch } from '../nodes/genes'

const QUERY_LIMIT = 500

const DATASETS = ['SGE', 'VAMP-seq', 'MutPred2', 'ESM-1v'] as const

const geneQueryFormat = genesCommonQueryFormat.merge(z.object({
  method: z.enum(DATASETS).optional(),
  files_fileset: z.string().optional()
})).merge(commonHumanEdgeParamsFormat).omit({ organism: true, verbose: true })

const allVariantsQueryFormat = z.object({
  gene_id: z.string(),
  dataset: z.enum(DATASETS),
  page: z.number().default(0),
  limit: z.number().optional()
})

const codingVariantsScoresFormat = z.object({
  variant: z.string().or(variantSimplifiedFormat),
  protein_change: z.object({
    coding_variant_id: z.string().nullish(),
    protein_id: z.string().nullish(),
    protein_name: z.string().nullish(),
    transcript_id: z.string().nullish(),
    hgvsp: z.string().nullish(),
    aapos: z.number().nullish(),
    ref: z.string().nullish(),
    alt: z.string().nullish()
  }).nullish(),
  scores: z.array(z.object({
    method: z.string(),
    score: z.number().nullish(),
    source_url: z.string().nullish()
  }))
})

const codingVariantCollectionName = 'coding_variants'
const codingVariantToPhenotypeCollectionName = 'coding_variants_phenotypes'
const variantSchema = getSchema('data/schemas/nodes/variants.Favor.json')
const geneCollectionName = 'genes'

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

  let limit = 500
  if (input.limit !== undefined) {
    limit = (input.limit as number <= QUERY_LIMIT) ? input.limit as number : QUERY_LIMIT
    delete input.limit
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
        SORT p.score DESC
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN p.score
    `
  } else if (input.dataset === 'VAMP-seq') {
    scoreQuery = `
      FOR p IN ${codingVariantToPhenotypeCollectionName}
        FILTER p._from IN codingVariantsIds && p.method == "VAMP-seq"
        SORT p.score DESC
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN p.score
    `
  } else if (input.dataset === 'ESM-1v') {
    scoreQuery = `
      FOR p IN ${codingVariantToPhenotypeCollectionName}
        FILTER p._from IN codingVariantsIds && p.method == "ESM-1v"
        SORT p.esm_1v_score DESC
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN p.esm_1v_score
    `
  } else if (input.dataset === 'MutPred2') {
    scoreQuery = `
      FOR p IN ${codingVariantToPhenotypeCollectionName}
        FILTER p._from IN codingVariantsIds && p.method == "MutPred2"
        SORT p.pathogenicity_score DESC
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN p.pathogenicity_score
    `
  }

  const query = `
    LET gene_name = DOCUMENT("${geneCollectionName}/${input.gene_id as string}").name

    LET codingVariantsIds = (
      FOR record IN ${codingVariantCollectionName}
      FILTER record.gene_name == gene_name
      RETURN record._id
    )

    ${scoreQuery}
  `

  return await ((await db.query(query)).all())
}

async function cachedFindCodingVariantsFromGenes (input: paramsFormatType, method: string | undefined): Promise<any> {
  if (method !== undefined) {
    const query = `
      LET doc = DOCUMENT(genes_coding_variants_scores, "${input.gene_id as string}")

      RETURN doc == null ? null : (
        FOR s IN doc.variant_scores || []
          FILTER "${method}" IN s.scores[*].method
          LIMIT ${input.page as number * (input.limit as number || 25)}, ${input.limit as number || 25}
          RETURN s
      )
    `

    let obj = await ((await db.query(query)).all())
    if (Array.isArray(obj) && obj.length > 0) {
      obj = obj[0]

      if (obj === null) {
        return undefined
      }

      obj.filter((item) => {
        const filteredScores = (item.scores as any[]).filter((score) => score.method === method)
        item.scores = filteredScores
        return item
      })

      return obj
    }

    return undefined
  }

  const query = `
    FOR doc IN genes_coding_variants_scores
      FILTER doc._key == "${input.gene_id as string}"
      RETURN SLICE(doc.variant_scores, ${input.page as number * (input.limit as number || 25)}, ${input.limit as number || 25})
  `

  const obj = await ((await db.query(query)).all())

  if (Array.isArray(obj) && obj.length > 0) {
    return obj[0]
  }
  return undefined
}

function validateInput (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['gene_id', 'hgnc_id', 'gene_name', 'alias'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one gene property must be defined.'
    })
  }
}

async function findCodingVariantsFromGenes (input: paramsFormatType): Promise<any[]> {
  validateInput(input)

  let limit = 25
  if (input.limit !== undefined) {
    limit = (input.limit as number <= QUERY_LIMIT) ? input.limit as number : QUERY_LIMIT
    delete input.limit
  }

  const method = input.method as string
  delete input.method
  const methodFilter = method !== undefined ? `AND p.method == "${method}"` : ''

  if (input.gene_id === undefined) {
    // since inputs are IDs, we are expecting len(genes) === 1 or 0
    input.name = input.gene_name
    delete input.gene_name

    const gene = await geneSearch(input)
    if (gene.length === 0) {
      return []
    }
    input.gene_id = gene[0]._id
  }

  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = ` AND v.files_filesets == 'files_filesets/${input.files_fileset as string}'`
  } else {
    const cachedValues = await cachedFindCodingVariantsFromGenes(input, method)
    if (cachedValues !== undefined) {
      return cachedValues
    }
  }

  // Score map: pathogenicity_score => MutPred2, esm_1v_score => ESM1, score => VampSeq
  const query = `
    LET gene_name = DOCUMENT("${geneCollectionName}/${input.gene_id as string}").name

    LET codingVariants = (
      FOR cv IN ${codingVariantCollectionName}
        FILTER cv.gene_name == gene_name
        RETURN cv._id
    )

    LET variantMap = (
      FOR vcv IN variants_coding_variants
        FILTER vcv._to IN codingVariants
        RETURN { codingVariant: vcv._to, variantId: vcv._from }
    )

    LET variantIds = UNIQUE(variantMap[*].variantId)

    LET variantData = (
      FOR v IN variants
      FILTER v._id IN variantIds
      RETURN {
        [v._id]: {${getDBReturnStatements(variantSchema, true).replaceAll('record', 'v')}}
      }
    )

    LET variantDict = MERGE(variantData)

    LET variantLookup = (
      FOR map IN variantMap
        RETURN { [map.codingVariant]: variantDict[map.variantId] }
    )

    LET variantByCodingVariant = MERGE(variantLookup)

    LET sgeResults = (
      FOR v IN variants_phenotypes_coding_variants
        FILTER v._to IN codingVariants ${filesetFilter} ${methodFilter.replace('p.', 'v.')}
        LET phenotype = DOCUMENT(v._from)
        LET fileset = DOCUMENT(v.files_filesets)
        RETURN {
          codingVariant: v._to,
          variant: variantByCodingVariant[v._to],
          score: phenotype.score,
          method: fileset.preferred_assay_titles[0],
          source_url: v.source_url
        }
    )

    LET otherResults = (
      FOR p IN ${codingVariantToPhenotypeCollectionName}
        FILTER p._from IN codingVariants ${filesetFilter.replace('v.', 'p.')} ${methodFilter}
        RETURN {
          codingVariant: p._from,
          variant: variantByCodingVariant[p._from],
          score: p.pathogenicity_score OR p.esm_1v_score OR p.score,
          method: p.method,
          source_url: p.source_url
        }
    )

    FOR doc IN UNION(sgeResults, otherResults)
      COLLECT variant = doc.variant, codingVariant = doc.codingVariant INTO grouped = doc
      LET cvDoc = DOCUMENT(codingVariant)
      LET maxScore = MAX(grouped[*].score)
      SORT maxScore DESC
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        variant,
        protein_change: {
          coding_variant_id: cvDoc._key,
          protein_id: cvDoc.protein_id,
          protein_name: cvDoc.protein_name,
          transcript_id: cvDoc.transcript_id,
          hgvsp: cvDoc.hgvsp,
          aapos: cvDoc.aapos,
          ref: cvDoc.ref,
          alt: cvDoc.alt
        },
        scores: grouped[* RETURN { method: CURRENT.method, score: CURRENT.score, source_url: CURRENT.source_url }]
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
