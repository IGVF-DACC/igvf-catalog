import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { studyFormat } from '../nodes/studies'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { QUERY_LIMIT } from '../../../constants'
import { db } from '../../../database'
import { TRPCError } from '@trpc/server'
import { variantIDSearch } from '../nodes/variants'
import { commonHumanEdgeParamsFormat, variantsCommonQueryFormat } from '../params'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 100

const variantsPhenotypesQueryFormat = z.object({
  phenotype_id: z.string().trim().optional(),
  log10pvalue: z.string().trim().optional()
})

const variantPhenotypeFormat = z.object({
  rsid: z.array(z.string()).nullish(),
  phenotype_term: z.string().nullable(),
  study: z.string().or(studyFormat).optional(),
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
  version: z.string().default('October 2022 (22.10)'),
  name: z.string()
})

const variantToPhenotypeCollectionName = 'variants_phenotypes'
const studySchema = getSchema('data/schemas/nodes/studies.GWAS.json')
const studyCollectionName = studySchema.db_collection_name as string
const variantPhenotypeToStudy = getSchema('data/schemas/edges/variants_phenotypes_studies.GWAS.json')
const variantPhenotypeToStudyCollectionName = variantPhenotypeToStudy.db_collection_name as string

export function variantQueryValidation (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id', 'chr', 'position', 'log10pvalue'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one variant property or log10pvalue must be defined.'
    })
  }
  if ((input.chr === undefined && input.position !== undefined) || (input.chr !== undefined && input.position === undefined)) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Chromosome and position must be defined together.'
    })
  }
}
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
  delete input.organism
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const verboseQuery = `
    FOR targetRecord IN ${studyCollectionName}
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
        For record IN ${variantToPhenotypeCollectionName}
        FILTER record._to == 'ontology_terms/${input.phenotype_id as string}'
        RETURN record._id
    )

    FOR edgeRecord IN ${variantPhenotypeToStudyCollectionName}
    FILTER edgeRecord._from IN primaryEdge ${pvalueFilter}
    SORT edgeRecord._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN {
      'study': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'edgeRecord._to'},
      ${getDBReturnStatements(variantPhenotypeToStudy).replaceAll('record', 'edgeRecord')},
      'name': edgeRecord.inverse_name // endpoint is opposite to ArangoDB collection name
    }
  `
  } else {
    if (input.phenotype_name !== undefined) {
      query = `
      LET primaryTerms = (
        FOR record IN ontology_terms_text_en_no_stem_inverted_search_alias
        SEARCH TOKENS("${input.phenotype_name as string}", "text_en_no_stem") ALL in record.name
        SORT BM25(record) DESC
        RETURN record._id
      )

      LET primaryEdge = (
        For record IN ${variantToPhenotypeCollectionName}
        FILTER record._to IN primaryTerms
        RETURN record._id
      )

      FOR edgeRecord IN ${variantPhenotypeToStudyCollectionName}
      FILTER edgeRecord._from IN primaryEdge ${pvalueFilter}
      SORT edgeRecord._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'study': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'edgeRecord._to'},
        ${getDBReturnStatements(variantPhenotypeToStudy).replaceAll('record', 'edgeRecord')},
        'name': edgeRecord.inverse_name // endpoint is opposite to ArangoDB collection name
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

async function findPhenotypesFromVariantSearch (input: paramsFormatType): Promise<any[]> {
  variantQueryValidation(input)
  delete input.organism
  let variantIDs = []
  const hasVariantQuery = Object.keys(input).some(item => ['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id', 'chr', 'position'].includes(item))
  if (hasVariantQuery) {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const variantInput: paramsFormatType = (({ variant_id, spdi, hgvs, ca_id, rsid, chr, position }) => ({ variant_id, spdi, hgvs, ca_id, rsid, chr, position }))(input)
    delete input.variant_id
    delete input.spdi
    delete input.hgvs
    delete input.rsid
    delete input.chr
    delete input.position
    delete input.ca_id
    variantIDs = await variantIDSearch(variantInput)
  }

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
    FOR targetRecord IN ${studyCollectionName}
      FILTER targetRecord._key == PARSE_IDENTIFIER(edgeRecord._to).key
      RETURN {${getDBReturnStatements(studySchema).replaceAll('record', 'targetRecord')}}
  `

  let query
  if (phenotypeFilter !== '') {
    phenotypeFilter = `and record._to == 'ontology_terms/${phenotypeFilter}'`
  }

  let hyperEdgeFilter = getHyperEdgeFilters(input)

  if (hasVariantQuery) {
    if (hyperEdgeFilter !== '') {
      hyperEdgeFilter = `and ${hyperEdgeFilter}`
    }

    query = `
      FOR record IN ${variantToPhenotypeCollectionName}
        FILTER record._from IN ['${variantIDs.join('\', \'')}']  ${phenotypeFilter}
        FOR edgeRecord IN ${variantPhenotypeToStudyCollectionName}
          FILTER edgeRecord._from == record._id ${hyperEdgeFilter.replaceAll('record', 'edgeRecord')}
          SORT '_key'
          LIMIT ${input.page as number * limit}, ${limit}
          RETURN {
            'rsid': DOCUMENT(record._from).rsid,
            'study': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'edgeRecord._to'},
            ${getDBReturnStatements(variantPhenotypeToStudy).replaceAll('record', 'edgeRecord')},
            'name': edgeRecord.name
          }
    `
  } else {
    query = `
      FOR record IN ${variantPhenotypeToStudyCollectionName}
      FILTER ${hyperEdgeFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'rsid': DOCUMENT((FOR vp in ${variantToPhenotypeCollectionName} FILTER vp._id == record._from RETURN vp._from)[0]).rsid,
        'study': ${input.verbose === 'true' ? `(${verboseQuery.replaceAll('edgeRecord', 'record')})[0]` : 'record._to'},
        ${getDBReturnStatements(variantPhenotypeToStudy)},
        'name': record.name
      }
    `
  }

  return await ((await db.query(query)).all())
}

const variantsFromPhenotypes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/phenotypes/variants', description: descriptions.phenotypes_variants } })
  .input((z.object({ phenotype_id: z.string().trim().optional(), phenotype_name: z.string().trim().optional(), log10pvalue: z.string().trim().optional() }).merge(commonHumanEdgeParamsFormat)))
  .output(z.array(variantPhenotypeFormat))
  .query(async ({ input }) => await findVariantsFromPhenotypesSearch(input))

const phenotypesFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/phenotypes', description: descriptions.variants_phenotypes } })
  .input(variantsCommonQueryFormat.merge(variantsPhenotypesQueryFormat).merge(commonHumanEdgeParamsFormat))
  .output(z.array(variantPhenotypeFormat))
  .query(async ({ input }) => await findPhenotypesFromVariantSearch(input))

export const variantsPhenotypesRouters = {
  variantsFromPhenotypes,
  phenotypesFromVariants
}
