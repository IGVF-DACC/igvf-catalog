import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { variantFormat, variantsQueryFormat } from '../nodes/variants'
import { studyFormat } from '../nodes/studies'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { QUERY_LIMIT } from '../../../constants'
import { db } from '../../../database'
import { TRPCError } from '@trpc/server'

const MAX_PAGE_SIZE = 100

const variantPhenotypeFormat = z.object({
  'sequence variant': z.string().or(z.array(variantFormat)).optional(),
  phenotype_term: z.string().nullable(),
  study: z.string().or(z.array(studyFormat)).optional(),
  log10pvalue: z.number().nullable(),
  p_val: z.number().nullable(),
  p_val_exponent: z.number().nullable(),
  p_val_mantissa: z.number().nullable(),
  beta: z.number().nullable(),
  beta_ci_lower: z.number().nullable(),
  beta_ci_upper: z.number().nullable(),
  oddsr_ci_lower: z.number().nullable(),
  oddsr_ci_upper: z.number().nullable(),
  lead_chrom: z.string().nullable(),
  lead_pos: z.number().nullable(),
  lead_ref: z.string().nullable(),
  lead_alt: z.string().nullable(),
  direction: z.string().nullable(),
  source: z.string().default('OpenTargets'),
  version: z.string().default('October 2022 (22.10)')
})

const schema = loadSchemaConfig()

const variantSchema = schema['sequence variant']
const variantToPhenotypeSchema = schema['variant to phenotype']
const studySchema = schema.study
const variantPhenotypeToStudy = schema['variant to phenotype to study']

// parse p-value filter on hyperedges from input
function getHyperEdgeFilters (input: paramsFormatType): string {
  let hyperEdgeFilter = ''
  if (input.log10pvalue !== undefined) {
    hyperEdgeFilter = `${getFilterStatements(variantPhenotypeToStudy, { log10pvalue: input.log10pvalue })}`
    delete input.log10pvalue
  }

  return hyperEdgeFilter
}

// Query for endpoint phenotypes/variants/, by phenotype query (allow fuzzy search), (AND p-value filter)
async function findVariantsFromPhenotypesSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const verboseQuery = `
    FOR targetRecord IN ${studySchema.db_collection_name}
      FILTER targetRecord._key == PARSE_IDENTIFIER(edgeRecord._to).key
      RETURN {${getDBReturnStatements(studySchema).replaceAll('record', 'targetRecord')}}
  `

  let pvalueFilter = getHyperEdgeFilters(input)
  if (pvalueFilter !== '') {
    pvalueFilter = `and ${pvalueFilter.replaceAll('record', 'edgeRecord')}`
  }

  let query = ''

  if (input.phenotype_id !== undefined) {
    query = `
    LET primaryEdge = (
        For record IN ${variantToPhenotypeSchema.db_collection_name}
        FILTER record._to == 'ontology_terms/${input.phenotype_id}'
        RETURN record._id
    )

    FOR edgeRecord IN ${variantPhenotypeToStudy.db_collection_name}
    FILTER edgeRecord._from IN primaryEdge ${pvalueFilter}
    SORT edgeRecord._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN {
      'study': ${input.verbose === 'true' ? `(${verboseQuery})` : 'edgeRecord._to'},
      ${getDBReturnStatements(variantPhenotypeToStudy).replaceAll('record', 'edgeRecord')}
    }
  `
  } else {
    if (input.phenotype_name !== undefined) {
      query = `
      LET primaryTerms = (
        FOR record IN ontology_terms_fuzzy_search_alias
        SEARCH TOKENS("${input.phenotype_name}", "text_en_no_stem") ALL in record.name
        SORT BM25(record) DESC
        RETURN record._id
      )

      LET primaryEdge = (
        For record IN ${variantToPhenotypeSchema.db_collection_name}
        FILTER record._to IN primaryTerms
        RETURN record._id
      )

      FOR edgeRecord IN ${variantPhenotypeToStudy.db_collection_name}
      FILTER edgeRecord._from IN primaryEdge ${pvalueFilter}
      SORT edgeRecord._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'study': ${input.verbose === 'true' ? `(${verboseQuery})` : 'edgeRecord._to'},
        ${getDBReturnStatements(variantPhenotypeToStudy).replaceAll('record', 'edgeRecord')}
      }
    `
    } else {
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: 'Either phnenotype id or phenotype name must be defined.'
      })
    }
  }

  return await ((await db.query(query)).all())
}

// Query for endpoint variants/phenotypes/, by p-value filter AND/OR variant query, (AND phenotype ontology id)
// could combine with variantSearch
async function getHyperedgeFromVariantQuery (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let phenotypeFilter = ''
  if (input.phenotype_id !== undefined) {
    phenotypeFilter = input.phenotype_id as string
    delete input.phenotype_id
  }

  const verboseQuery = `
    FOR targetRecord IN ${studySchema.db_collection_name}
      FILTER targetRecord._key == PARSE_IDENTIFIER(edgeRecord._to).key
      RETURN {${getDBReturnStatements(studySchema).replaceAll('record', 'targetRecord')}}
  `

  let query
  if (phenotypeFilter !== '') {
    phenotypeFilter = `and record._to == 'ontology_terms/${phenotypeFilter}'`
  }

  let queryOptions = ''
  if (input.pos !== undefined) {
    queryOptions = 'OPTIONS { indexHint: "region", forceIndexHint: true }'
  }

  let hyperEdgeFilter = getHyperEdgeFilters(input)
  const variantFilters = getFilterStatements(variantSchema, input)

  if (variantFilters !== '') {
    if (hyperEdgeFilter !== '') {
      hyperEdgeFilter = `and ${hyperEdgeFilter}`
    }
    // variant_id overwrites other fields query on variant
    if (input._key !== undefined) {
      query = `
      LET primaryEdges = (
        FOR record IN ${variantToPhenotypeSchema.db_collection_name}
        FILTER record._from == 'variants/${input._key as string}' ${phenotypeFilter}
        RETURN record._id
      )

      FOR edgeRecord IN ${variantPhenotypeToStudy.db_collection_name}
      FILTER edgeRecord._from IN primaryEdges ${hyperEdgeFilter.replaceAll('record', 'edgeRecord')}
      SORT '_key'
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'study': ${input.verbose === 'true' ? `(${verboseQuery})` : 'edgeRecord._to'},
        ${getDBReturnStatements(variantPhenotypeToStudy).replaceAll('record', 'edgeRecord')}
      }
      `
    } else {
      query = `
      LET primarySources = (
        FOR record IN ${variantSchema.db_collection_name} ${queryOptions}
        FILTER ${variantFilters}
        RETURN record._id
      )

      LET primaryEdges = (
        FOR record IN ${variantToPhenotypeSchema.db_collection_name}
        FILTER record._from IN primarySources ${phenotypeFilter}
        RETURN record._id
      )

      FOR edgeRecord IN ${variantPhenotypeToStudy.db_collection_name}
      FILTER edgeRecord._from IN primaryEdges ${hyperEdgeFilter.replaceAll('record', 'edgeRecord')}
      SORT '_key'
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'study': ${input.verbose === 'true' ? `(${verboseQuery})` : 'edgeRecord._to'},
        ${getDBReturnStatements(variantPhenotypeToStudy).replaceAll('record', 'edgeRecord')}
      }
      `
    }
  } else {
    if (hyperEdgeFilter !== '') {
      query = `
        FOR record IN ${variantPhenotypeToStudy.db_collection_name}
        FILTER ${hyperEdgeFilter}
        SORT record._key
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN {
          'study': ${input.verbose === 'true' ? `(${verboseQuery})` : 'record._to'},
          ${getDBReturnStatements(variantPhenotypeToStudy)}
        }
      `
    } else {
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: 'At least one filter on variant or log10pvalue must be defined.'
      })
    }
  }

  return await ((await db.query(query)).all())
}

async function findPhenotypesFromVariantSearch (input: paramsFormatType): Promise<any[]> {
  if (input.variant_id !== undefined) {
    input._key = input.variant_id
    delete input.variant_id
  }

  if (input.funseq_description !== undefined) {
    input['annotations.funseq_description'] = input.funseq_description
    delete input.funseq_description
  }

  if (input.source !== undefined) {
    input[`annotations.freq.${input.source}.alt`] = `range:${input.min_alt_freq as string}-${input.max_alt_freq as string}`
    delete input.min_alt_freq
    delete input.max_alt_freq
    delete input.source
  }

  return await getHyperedgeFromVariantQuery(preProcessRegionParam(input, 'pos'))
}

const variantsFromPhenotypes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/phenotypes/variants', description: descriptions.phenotypes_variants } })
  .input((z.object({ phenotype_id: z.string().trim().optional(), phenotype_name: z.string().trim().optional(), log10pvalue: z.string().trim().optional(), page: z.number().default(0), limit: z.number().optional(), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(variantPhenotypeFormat))
  .query(async ({ input }) => await findVariantsFromPhenotypesSearch(input))

const phenotypesFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/phenotypes', description: descriptions.variants_phenotypes } })
  .input(variantsQueryFormat.merge(z.object({ phenotype_id: z.string().trim().optional(), log10pvalue: z.string().trim().optional(), limit: z.number().optional(), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(variantPhenotypeFormat))
  .query(async ({ input }) => await findPhenotypesFromVariantSearch(input))

export const variantsPhenotypesRouters = {
  variantsFromPhenotypes,
  phenotypesFromVariants
}
