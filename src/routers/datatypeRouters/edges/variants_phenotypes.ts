import { z } from 'zod'
import { publicProcedure, router } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { variantFormat, variantsQueryFormat } from '../nodes/variants'
import { ontologyFormat, ontologyQueryFormat } from '../nodes/ontologies'
import { studyFormat } from '../nodes/studies'
import { paramsFormatType, preProcessRegionParam } from '../_helpers'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
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

const phenotypeSchema = schema['ontology term']
const edgeSchema = schema['variant to phenotype']
const studySchema = schema.study
const hyperEdgeSchema = schema['variant to phenotype to study']

// do we still need routerEdge?
const routerEdge = new RouterEdges(edgeSchema, new RouterEdges(hyperEdgeSchema))
// const studyRouter = new RouterFilterBy(studyObj)

// Query for endpoint variants/phenotypes/, by p-value filter AND/OR variant query, (AND phenotype ontology id)
async function getHyperedgeFromVariantQuery (router: RouterEdges, input: paramsFormatType, phenotypeFilter = '', hyperEdgeFilter = '', queryOptions = '', page: number = 0, verbose: boolean, sortBy: string = '_key'): Promise<any[]> {
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
      SORT '${sortBy}'
      LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN {
        'study': ${verbose ? `(${verboseQuery})` : 'edgeRecord._to'},
        ${router.secondaryRouter?.dbReturnStatements.replaceAll('record', 'edgeRecord') as string}
      }
      `
  } else {
    if (hyperEdgeFilter !== '') {
      query = `
        FOR record IN ${variantPhenotypeStudyCollection}
        FILTER ${hyperEdgeFilter}
        SORT '${sortBy}'
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN {
          'study': ${verbose ? `(${verboseQuery})` : 'record._to'},
          ${router.secondaryRouter?.dbReturnStatements as string}
        }
      `
    } else {
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: 'At least one property must be defined.'
      })
    }
  }

  console.log(query)
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
  const hyperEdgeFilters = await getHyperEdgeFilters(input)
  // should preProcessRegionParam in input? it's also in filterStatements
  return await getHyperedgeFromVariantQuery(routerEdge, preProcessRegionParam(input, 'pos'), phenotypeFilter, hyperEdgeFilters, queryOptions, input.page as number, input.verbose === 'true')
}

// parse p-value filter on hyperedges from input
async function getHyperEdgeFilters (input: paramsFormatType): Promise<string> {
  const hyperEdgeFilters = []

  if (input.log10pvalue !== undefined) {
    hyperEdgeFilters.push(`${routerEdge.secondaryRouter?.getFilterStatements({ log10pvalue: input.log10pvalue }) as string}`)
    delete input.log10pvalue
  }

  return hyperEdgeFilters.join(' and ')
}

const variantsFromPhenotypes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/phenotypes/variants', description: descriptions.phenotypes_variants } })
  .input(ontologyQueryFormat.omit({ source: true, subontology: true }).merge(z.object({ log10pvalue: z.string().trim().optional(), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(variantPhenotypeFormat))
  .query(async ({ input }) => await routerEdge.getPrimaryTargetsFromHyperEdge(input, input.page, '_key', await studySearchFilters(input), input.verbose === 'true'))

const phenotypesFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/phenotypes', description: descriptions.variants_phenotypes } })
  .input(variantsQueryFormat.merge(z.object({ phenotype_id: z.string().trim().optional(), log10pvalue: z.string().trim().optional(), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(variantPhenotypeFormat))
  .query(async ({ input }) => await variantSearch(input))

export const variantsPhenotypesRouters = {
  variantsFromPhenotypes,
  phenotypesFromVariants
}
