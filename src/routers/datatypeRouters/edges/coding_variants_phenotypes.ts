import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { QUERY_LIMIT } from '../../../constants'
import { db } from '../../../database'
import { TRPCError } from '@trpc/server'
import { commonHumanEdgeParamsFormat } from '../params'
import { ontologyFormat } from '../nodes/ontologies'
import { variantReturnFormat } from './variants_diseases'

const MAX_PAGE_SIZE = 100

const geneQueryFormat = z.object({
  gene_id: z.string().optional()
})

const codingVariantsPhenotypeAggregationFormat = z.object({
  source: z.string(),
  count: z.number()
})

const fromCodingVariantsQueryFormat = z.object({
  coding_variant_name: z.string().optional(),
  hgvsp: z.string().optional(),
  protein_name: z.string().optional(),
  gene_name: z.string().optional(),
  amino_acid_position: z.number().optional(),
  transcript_id: z.string().optional()
})

const codingVariantsFormat = z.object({
  _id: z.string(),
  name: z.string(),
  ref: z.string().nullish(),
  alt: z.string().nullish(),
  protein_name: z.string().nullish(),
  gene_name: z.string().nullish(),
  transcript_id: z.string().nullish(),
  aapos: z.number().nullish(),
  hgvsp: z.string().nullish(),
  hgvs: z.string().nullish(),
  ref_codon: z.string().nullish(),
  codonpos: z.number().nullish(),
  SIFT_score: z.number().nullish(),
  SIFT4G_score: z.number().nullish(),
  Polyphen2_HDIV_score: z.number().nullish(),
  Polyphen2_HVAR_score: z.number().nullish(),
  VEST4_score: z.number().nullish(),
  Mcap_score: z.number().nullish(),
  REVEL_score: z.number().nullish(),
  MutPred_score: z.number().nullish(),
  BayesDel_addAF_score: z.number().nullish(),
  BayesDel_noAF_score: z.number().nullish(),
  VARITY_R_score: z.number().nullish(),
  VARITY_ER_score: z.number().nullish(),
  VARITY_R_LOO_score: z.number().nullish(),
  VARITY_ER_LOO_score: z.number().nullish(),
  ESM1b_score: z.number().nullish(),
  EVE_score: z.number().nullish(),
  AlphaMissense_score: z.number().nullish(),
  CADD_raw_score: z.number().nullish(),
  source: z.string(),
  source_url: z.string()
})

const outputFormat = z.object({
  coding_variant: z.string().or(codingVariantsFormat).nullish(),
  variant: z.string().or(variantReturnFormat).optional(),
  phenotype: z.string().or(ontologyFormat).optional(),
  score: z.number().nullable(),
  source: z.string(),
  source_url: z.string()
})

const schema = loadSchemaConfig()
const codingVariantToPhenotypeSchema = schema['coding variant to phenotype']
const codingVariantSchema = schema['coding variant']
const ontologySchema = schema['ontology term']
const geneSchema = schema.gene

function variantQueryValidation (input: paramsFormatType): void {
  const validKeys = ['coding_variant_name', 'hgvsp', 'protein_name', 'gene_name', 'amino_acid_position', 'transcript_id'] as const

  // Count how many keys are defined in input
  const definedKeysCount = validKeys.filter(key => key in input && input[key] !== undefined).length

  if (definedKeysCount < 1) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'None of the coding variant properties is defined.'
    })
  }
}

function phenotypeQueryValidation (input: paramsFormatType): void {
  const validKeys = ['phenotype_id', 'phenotype_name'] as const

  // Count how many keys are defined in input
  const definedKeysCount = validKeys.filter(key => key in input && input[key] !== undefined).length

  if (definedKeysCount < 1) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'None of the phenotype properties is defined.'
    })
  }
}

async function findCodingVariantsFromPhenotypesSearch (input: paramsFormatType): Promise<any[]> {
  phenotypeQueryValidation(input)
  delete input.organism
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  if (input.phenotype_id !== undefined) {
    input._key = input.phenotype_id
    delete input.phenotype_id
  }

  if (input.phenotype_name !== undefined) {
    input.name = input.phenotype_name
    delete input.phenotype_name
  }
  const phenotypeFilters = getFilterStatements(ontologySchema, input)

  let query = `
    FOR record In ${ontologySchema.db_collection_name as string}
      FILTER ${phenotypeFilters}

      LET a = (
        FOR phenoEdges IN coding_variants_phenotypes
          FILTER phenoEdges._to == record._id
          FOR variantEdge IN variants_coding_variants
            FILTER variantEdge._to == phenoEdges._from
            RETURN {
              'coding_variant': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._from)' : 'phenoEdges._from'},
              'phenotype': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._to)' : 'phenoEdges._to'},
              'score': phenoEdges.abundance_score,
              'source': phenoEdges.source,
              'source_url': phenoEdges.source_url,
              'variant': ${input.verbose === 'true' ? 'DOCUMENT(variantEdge._from)' : 'variantEdge._from'}
            }
      )

      LET b = (
        FOR phenoEdges IN variants_phenotypes
          FILTER phenoEdges._to == record._id
          FOR cpcv IN variants_phenotypes_coding_variants
            FILTER cpcv._from == phenoEdges._id
            RETURN {
              'coding_variant': ${input.verbose === 'true' ? 'DOCUMENT(cpcv._to)' : 'cpcv._to'},
              'phenotype': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._to)' : 'phenoEdges._to'},
              'variant': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._from)' : 'phenoEdges._from'},
              'score': phenoEdges.score,
              'source': phenoEdges.source,
              'source_url': phenoEdges.source_url
            }
      )

      LET combined = UNION(a, b)
      RETURN SLICE(combined, ${input.page as number * limit}, ${limit})
  `
  let objects = await ((await db.query(query)).all())

  if (objects.length === 0 && input.name !== undefined) {
    query = `
      LET primaryTerms = (
        FOR record IN ontology_terms_text_en_no_stem_inverted_search_alias
        SEARCH TOKENS("${input.name as string}", "text_en_no_stem") ALL in record.name
        SORT BM25(record) DESC
        RETURN record._id
      )

      LET a = (
        FOR phenoEdges IN coding_variants_phenotypes
          FILTER phenoEdges._to IN primaryTerms
          FOR variantEdge IN variants_coding_variants
            FILTER variantEdge._to == phenoEdges._from
            RETURN {
              'coding_variant': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._from)' : 'phenoEdges._from'},
              'phenotype': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._to)' : 'phenoEdges._to'},
              'score': phenoEdges.abundance_score,
              'source': phenoEdges.source,
              'source_url': phenoEdges.source_url,
              'variant': ${input.verbose === 'true' ? 'DOCUMENT(variantEdge._from)' : 'variantEdge._from'}
            }
      )

      LET b = (
        FOR phenoEdges IN variants_phenotypes
          FILTER phenoEdges._to IN primaryTerms
          FOR cpcv IN variants_phenotypes_coding_variants
            FILTER cpcv._from == phenoEdges._id
            RETURN {
              'coding_variant': ${input.verbose === 'true' ? 'DOCUMENT(cpcv._to)' : 'cpcv._to'},
              'phenotype': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._to)' : 'phenoEdges._to'},
              'variant': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._from)' : 'phenoEdges._from'},
              'score': phenoEdges.score,
              'source': phenoEdges.source,
              'source_url': phenoEdges.source_url
            }
      )

      LET combined = UNION(a, b)
      RETURN SLICE(combined, ${input.page as number * limit}, ${limit})
    `
    objects = await ((await db.query(query)).all())
  }

  return objects[0] || []
}

async function findPhenotypesFromCodingVariantSearch (input: paramsFormatType): Promise<any[]> {
  variantQueryValidation(input)
  delete input.organism

  if (input.amino_acid_position !== undefined) {
    input.aapos = input.amino_acid_position
    delete input.amino_acid_position
  }
  if (input.coding_variant_name !== undefined) {
    // replace ">" with "-" in coding_variant_name
    input.name = (input.coding_variant_name as string).replace('>', '-')
    delete input.coding_variant_name
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  let sourceFilter = ''
  if (input.source !== undefined) {
    sourceFilter = `AND phenoEdges.source == '${input.source as string}'`
    delete input.source
  }

  let variantFilters = getFilterStatements(codingVariantSchema, input)

  if (variantFilters !== '') {
    variantFilters = `FILTER ${variantFilters}`
  }

  const query = `
  FOR record IN coding_variants
    ${variantFilters}

    LET variantEdges = (
      FOR ve IN variants_coding_variants
        FILTER ve._to == record._id
        RETURN ve._from
    )

    LET a = (
      FOR phenoEdges IN coding_variants_phenotypes
        FILTER phenoEdges._from == record._id
        ${sourceFilter}

        FOR variantId IN variantEdges
          RETURN {
            'coding_variant': ${input.verbose === 'true' ? 'DOCUMENT(record._id)' : 'record._id'},
            'phenotype': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._to)' : 'phenoEdges._to'},
            'variant': ${input.verbose === 'true' ? 'DOCUMENT(variantId)' : 'variantId'},
            'score': phenoEdges.abundance_score,
            'source': phenoEdges.source,
            'source_url': phenoEdges.source_url
          }
    )

    LET b = (
      FOR cpcv IN variants_phenotypes_coding_variants
        FILTER cpcv._to == record._id
        FOR phenoEdges IN variants_phenotypes
          FILTER phenoEdges._id == cpcv._from
          RETURN {
            'coding_variant': ${input.verbose === 'true' ? 'DOCUMENT(record._id)' : 'record._id'},
            'phenotype': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._to)' : 'phenoEdges._to'},
            'variant': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._from)' : 'phenoEdges._from'},
            'score': phenoEdges.score,
            'source': phenoEdges.source,
            'source_url': phenoEdges.source_url
          }
    )

    LET combined = UNION(a, b)
    RETURN SLICE(combined, ${input.page as number * limit}, ${limit})
  `

  const objs = await ((await db.query(query)).all())
  return objs[0] || []
}

async function countCodingVariantsFromGene (input: paramsFormatType): Promise<any[]> {
  if (input.gene_id === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'gene_id is required'
    })
  }

  const query = `
    LET gene_name = DOCUMENT('${geneSchema.db_collection_name as string}/${input.gene_id as string}').name

    LET codingVariants = (
      FOR record IN ${codingVariantSchema.db_collection_name as string}
      FILTER record.gene_name == gene_name
      RETURN record._id
    )

    LET sge = (
      FOR v IN variants_phenotypes_coding_variants
        FILTER v._to IN codingVariants
        COLLECT fileset_id = v.files_filesets WITH COUNT INTO count
        LET fileset = DOCUMENT(fileset_id)
        RETURN { source: fileset.preferred_assay_titles[0], count: count }
    )

    LET vampseq = (
      FOR phenoEdges IN ${codingVariantToPhenotypeSchema.db_collection_name as string}
        FILTER phenoEdges._from IN codingVariants
        COLLECT src = phenoEdges.source WITH COUNT INTO count
        RETURN { source: src, count: count }
    )

    RETURN UNION(sge, vampseq)
  `

  const objs = await ((await db.query(query)).all())
  return objs[0] || []
}

const codingVariantsFromPhenotypes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/phenotypes/coding-variants', description: descriptions.phenotypes_coding_variants } })
  .input((z.object({ phenotype_id: z.string().trim().optional(), phenotype_name: z.string().trim().optional() }).merge(commonHumanEdgeParamsFormat)))
  .output(z.array(outputFormat))
  .query(async ({ input }) => await findCodingVariantsFromPhenotypesSearch(input))

const phenotypesFromCodingVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/coding-variants/phenotypes', description: descriptions.coding_variants_phenotypes } })
  .input(fromCodingVariantsQueryFormat.merge(commonHumanEdgeParamsFormat))
  .output(z.array(outputFormat))
  .query(async ({ input }) => await findPhenotypesFromCodingVariantSearch(input))

const codingVariantsCountFromGene = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/coding-variants/phenotypes-count', description: descriptions.coding_variants_phenotypes_count } })
  .input(geneQueryFormat)
  .output(z.array(codingVariantsPhenotypeAggregationFormat))
  .query(async ({ input }) => await countCodingVariantsFromGene(input))

export const codingVariantsPhenotypesRouters = {
  codingVariantsFromPhenotypes,
  phenotypesFromCodingVariants,
  codingVariantsCountFromGene
}
