import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { variantFormat, variantsQueryFormat } from '../nodes/variants'
import { ontologyFormat } from '../nodes/ontologies'
import { studyFormat } from '../nodes/studies'
import { paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { QUERY_LIMIT } from '../../../constants'
import { db } from '../../../database'
import { TRPCError } from '@trpc/server'

// should we denormalize trait under variants_phenotypes_studies?
const variantPhenotypeFormat = z.object({
  'sequence variant': z.string().or(z.array(variantFormat)).optional(),
  'ontology term': z.string().or(z.array(ontologyFormat)).optional(),
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

const edgeSchema = schema['variant to phenotype']
const studySchema = schema.study
const hyperEdgeSchema = schema['variant to phenotype to study']

const routerEdge = new RouterEdges(edgeSchema, new RouterEdges(hyperEdgeSchema))

// Query for endpoint phenotypes/variants/, by phenotype query (allow fuzzy search), (AND p-value filter)
async function getHyperedgeFromPhenotypeQuery (router: RouterEdges, input: paramsFormatType): Promise<any[]> {
  const hyperEdgeFilters = getHyperEdgeFilters(router, input)
  const page = input.page as number
  const variantPhenotypeCollection = edgeSchema.db_collection_name as string
  const studyCollection = studySchema.db_collection_name as string
  const variantPhenotypeStudyCollection = hyperEdgeSchema.db_collection_name as string

  const studyReturn = router.secondaryRouter?.targetReturnStatements as string

  const verboseQuery = `
    FOR targetRecord IN ${studyCollection}
      FILTER targetRecord._key == PARSE_IDENTIFIER(edgeRecord._to).key
      RETURN {${studyReturn.replaceAll('record', 'targetRecord')}}
  `

  let pvalueFilter = ''
  if (hyperEdgeFilters !== '') {
    pvalueFilter = `and ${hyperEdgeFilters}`
  }

  let query = ''

  if (input.phenotype_id !== undefined) {
    query = `
    LET primaryEdge = (
        For record IN ${variantPhenotypeCollection}
        FILTER record._to == 'ontology_terms/${input.phenotype_id}'
        RETURN record._id
    )

    FOR edgeRecord IN ${variantPhenotypeStudyCollection}
    FILTER edgeRecord._from IN primaryEdge ${pvalueFilter.replaceAll('record', 'edgeRecord')}
    SORT '_key'
    LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
    RETURN (
      FOR record IN ${variantPhenotypeCollection}
      FILTER record._key == PARSE_IDENTIFIER(edgeRecord._from).key
      RETURN {
        'ontology term': DOCUMENT(record._to).name,
        'study': ${input.verbose === 'true' ? `(${verboseQuery})` : 'edgeRecord._to'},
        ${router.secondaryRouter?.dbReturnStatements.replaceAll('record', 'edgeRecord') as string}
      }
    )[0]
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
        For record IN ${variantPhenotypeCollection}
        FILTER record._to IN primaryTerms
        RETURN record._id
      )

      FOR edgeRecord IN ${variantPhenotypeStudyCollection}
      FILTER edgeRecord._from IN primaryEdge ${pvalueFilter.replaceAll('record', 'edgeRecord')}
      SORT '_key'
      LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN (
        FOR record IN ${variantPhenotypeCollection}
        FILTER record._key == PARSE_IDENTIFIER(edgeRecord._from).key
        RETURN {
          'ontology term': DOCUMENT(record._to).name,
          'study': ${input.verbose === 'true' ? `(${verboseQuery})` : 'edgeRecord._to'},
          ${router.secondaryRouter?.dbReturnStatements.replaceAll('record', 'edgeRecord') as string}
        }
      )[0]
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
async function getHyperedgeFromVariantQuery (router: RouterEdges, input: paramsFormatType, phenotypeFilter = '', hyperEdgeFilter = '', queryOptions = ''): Promise<any[]> {
  const variantCollection = variantSchema.db_collection_name as string
  const variantPhenotypeCollection = edgeSchema.db_collection_name as string
  const variantPhenotypeStudyCollection = hyperEdgeSchema.db_collection_name as string
  const studyCollection = studySchema.db_collection_name as string
  const variantFilters = router.filterStatements(input, router.sourceSchema)

  const studyReturn = router.secondaryRouter?.targetReturnStatements as string

  const verboseQuery = `
    FOR targetRecord IN ${studyCollection}
      FILTER targetRecord._key == PARSE_IDENTIFIER(edgeRecord._to).key
      RETURN {${studyReturn.replaceAll('record', 'targetRecord')}}
  `
  const page = input.page as number

  let query
  if (phenotypeFilter !== '') {
    phenotypeFilter = `and record._to == 'ontology_terms/${phenotypeFilter}'`
  }

  if (variantFilters !== '') {
    if (hyperEdgeFilter !== '') {
      hyperEdgeFilter = `and ${hyperEdgeFilter}`
    }
    query = `
      LET primarySources = (
        FOR record IN ${variantCollection} ${queryOptions}
        FILTER ${variantFilters}
        RETURN record._id
      )

      LET primaryEdges = (
        FOR record IN ${variantPhenotypeCollection}
        FILTER record._from IN primarySources ${phenotypeFilter}
        RETURN record._id
      )

      FOR edgeRecord IN ${variantPhenotypeStudyCollection}
      FILTER edgeRecord._from IN primaryEdges ${hyperEdgeFilter.replaceAll('record', 'edgeRecord')}
      SORT '_key'
      LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN (
        FOR record IN ${variantPhenotypeCollection}
        FILTER record._key == PARSE_IDENTIFIER(edgeRecord._from).key
        RETURN {
          'ontology term': DOCUMENT(record._to).name,
          'study': ${input.verbose === 'true' ? `(${verboseQuery})` : 'edgeRecord._to'},
          ${router.secondaryRouter?.dbReturnStatements.replaceAll('record', 'edgeRecord') as string}
        }
      )[0]
      `
  } else {
    if (hyperEdgeFilter !== '') {
      query = `
        FOR edgeRecord IN ${variantPhenotypeStudyCollection}
        FILTER ${hyperEdgeFilter}
        SORT '_key'
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN (
          FOR record IN ${variantPhenotypeCollection}
          FILTER record._key == PARSE_IDENTIFIER(edgeRecord._from).key
          RETURN {
            'ontology term': DOCUMENT(record._to).name,
            'study': ${input.verbose === 'true' ? `(${verboseQuery})` : 'edgeRecord._to'},
            ${router.secondaryRouter?.dbReturnStatements.replaceAll('record', 'edgeRecord') as string}
          }
        )[0]
      `
    } else {
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: 'At least one property must be defined.'
      })
    }
  }

  return await ((await db.query(query)).all())
}

async function variantSearch (input: paramsFormatType): Promise<any[]> {
  let queryOptions = ''
  if (input.region !== undefined) {
    queryOptions = 'OPTIONS { indexHint: "region", forceIndexHint: true }'
  }

  if (input.variant_id !== undefined) {
    input._key = input.variant_id // or do we want to make _id query overwrites other queries?
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
  let phenotypeFilter = ''
  if (input.phenotype_id !== undefined) {
    phenotypeFilter = input.phenotype_id as string
    delete input.phenotype_id
  }
  const hyperEdgeFilters = getHyperEdgeFilters(routerEdge, input)
  return await getHyperedgeFromVariantQuery(routerEdge, preProcessRegionParam(input, 'pos'), phenotypeFilter, hyperEdgeFilters, queryOptions)
}

// parse p-value filter on hyperedges from input
function getHyperEdgeFilters (router: RouterEdges, input: paramsFormatType): string {
  if (input.log10pvalue !== undefined) {
    delete input.log10pvalue
    return (`${router.secondaryRouter?.getFilterStatements({ log10pvalue: input.log10pvalue }) as string}`)
  }

  return ''
}

const variantsFromPhenotypes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/phenotypes/variants', description: descriptions.phenotypes_variants } })
  .input((z.object({ phenotype_id: z.string().trim().optional(), phenotype_name: z.string().trim().optional(), log10pvalue: z.string().trim().optional(), page: z.number().default(0), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(variantPhenotypeFormat))
  .query(async ({ input }) => await getHyperedgeFromPhenotypeQuery(routerEdge, input))

const phenotypesFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/phenotypes', description: descriptions.variants_phenotypes } })
  .input(variantsQueryFormat.merge(z.object({ phenotype_id: z.string().trim().optional(), log10pvalue: z.string().trim().optional(), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(variantPhenotypeFormat))
  .query(async ({ input }) => await variantSearch(input))

export const variantsPhenotypesRouters = {
  variantsFromPhenotypes,
  phenotypesFromVariants
}
