import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { QUERY_LIMIT } from '../../../constants'
import { db } from '../../../database'
import { TRPCError } from '@trpc/server'
import { commonHumanEdgeParamsFormat } from '../params'
import { ontologyFormat } from '../nodes/ontologies'
import { variantReturnFormat } from './variants_diseases'

const MAX_PAGE_SIZE = 100

const fromCodingVariantsQueryFormat = z.object({
  coding_variant_name: z.string().optional(),
  hgvsp: z.string().optional(),
  protein_name: z.string().optional(),
  gene_name: z.string().optional(),
  amino_acid_position: z.number().optional(),
  transcript_id: z.string().optional()
})

const edgeQueryFormat = z.object({
  source: z.enum(['VAMP-seq']).optional()
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

const OutputFormat = z.object({
  coding_variant: z.string().or(codingVariantsFormat).optional(),
  variant: z.string().or(variantReturnFormat).optional(),
  phenotype: z.string().or(ontologyFormat).optional(),
  abundance_score: z.number().nullable(),
  abundance_sd: z.number().nullable(),
  abundance_se: z.number().nullable(),
  ci_upper: z.number().nullable(),
  ci_lower: z.number().nullable(),
  abundance_Rep1: z.number().nullable(),
  abundance_Rep2: z.number().nullable(),
  abundance_Rep3: z.number().nullable(),
  source: z.string().default('VAMP-seq'),
  source_url: z.string().nullable()
})

const schema = loadSchemaConfig()
const codingVariantToPhenotypeSchema = schema['coding variant to phenotype']
const codingVariantSchema = schema['coding variant']
const ontologySchema = schema['ontology term']

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

  let sourceFilter = ''
  if (input.source !== undefined) {
    sourceFilter = `phenoEdges.source == '${input.source as string}'`
    delete input.source
  }
  let exactMatchSourceFilter = ''
  if (sourceFilter !== '') {
    exactMatchSourceFilter = `FILTER ${sourceFilter}`
  }
  let textSearchSourceFilter = ''
  if (sourceFilter !== '') {
    textSearchSourceFilter = `AND ${sourceFilter}`
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
    For phenoEdges IN ${codingVariantToPhenotypeSchema.db_collection_name as string}
      ${exactMatchSourceFilter}
      FOR variantEdge IN variants_coding_variants
        FILTER variantEdge._to == phenoEdges._from
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN {
        'coding_variant': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._from)' : 'phenoEdges._from'},
        'phenotype': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._to)' : 'phenoEdges._to'},
        ${getDBReturnStatements(codingVariantToPhenotypeSchema).replaceAll('record', 'phenoEdges')},
        "variant": ${input.verbose === 'true' ? 'DOCUMENT(variantEdge._from)' : 'variantEdge._from'}
        }
  `
  const objects = await ((await db.query(query)).all())
  if (objects.length === 0 && input.name !== undefined) {
    query = `
      LET primaryTerms = (
        FOR record IN ontology_terms_text_en_no_stem_inverted_search_alias
        SEARCH TOKENS("${input.name as string}", "text_en_no_stem") ALL in record.name
        SORT BM25(record) DESC
        RETURN record._id
      )

    FOR phenoEdges IN coding_variants_phenotypes
    FILTER phenoEdges._to in primaryTerms
    ${textSearchSourceFilter}

    FOR variantEdge IN variants_coding_variants
    FILTER variantEdge._to == phenoEdges._from
    limit ${input.page as number * limit}, ${limit}

        RETURN {
        'coding_variant': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._from)' : 'phenoEdges._from'},
        'phenotype': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._to)' : 'phenoEdges._to'},
        ${getDBReturnStatements(codingVariantToPhenotypeSchema).replaceAll('record', 'phenoEdges')},
        "variant": ${input.verbose === 'true' ? 'DOCUMENT(variantEdge._from)' : 'variantEdge._from'}
        }
    `
    const res = await ((await db.query(query)).all())
    return res
  }
  return objects
}

async function findPhenotypesFromCodingVariantSearch (input: paramsFormatType): Promise<any[]> {
  variantQueryValidation(input)
  delete input.organism
  let limit = QUERY_LIMIT
  if (input.amino_acid_position !== undefined) {
    input.aapos = input.amino_acid_position
    delete input.amino_acid_position
  }
  if (input.coding_variant_name !== undefined) {
    input.name = input.coding_variant_name
    delete input.coding_variant_name
  }

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

  FOR phenoEdges IN coding_variants_phenotypes
    FILTER phenoEdges._from == record._id
    ${sourceFilter}

    FOR variantEdge IN variants_coding_variants
      FILTER variantEdge._to == record._id
      limit ${input.page as number * limit}, ${limit}

        RETURN {
        'coding_variant': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._from)' : 'phenoEdges._from'},
        'phenotype': ${input.verbose === 'true' ? 'DOCUMENT(phenoEdges._to)' : 'phenoEdges._to'},
        ${getDBReturnStatements(codingVariantToPhenotypeSchema).replaceAll('record', 'phenoEdges')},
        "variant": ${input.verbose === 'true' ? 'DOCUMENT(variantEdge._from)' : 'variantEdge._from'}
        }
    `
  return await ((await db.query(query)).all())
}

const variantsFromPhenotypes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/phenotypes/coding-variants', description: descriptions.phenotypes_coding_variants } })
  .input((z.object({ phenotype_id: z.string().trim().optional(), phenotype_name: z.string().trim().optional() }).merge(edgeQueryFormat).merge(commonHumanEdgeParamsFormat)))
  .output(z.array(OutputFormat))
  .query(async ({ input }) => await findCodingVariantsFromPhenotypesSearch(input))

const phenotypesFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/coding-variants/phenotypes', description: descriptions.coding_variants_phenotypes } })
  .input(fromCodingVariantsQueryFormat.merge(edgeQueryFormat).merge(commonHumanEdgeParamsFormat))
  .output(z.array(OutputFormat))
  .query(async ({ input }) => await findPhenotypesFromCodingVariantSearch(input))

export const codingVariantsPhenotypesRouters = {
  variantsFromPhenotypes,
  phenotypesFromVariants
}
