import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { studyFormat } from '../nodes/studies'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { QUERY_LIMIT } from '../../../constants'
import { db } from '../../../database'
import { TRPCError } from '@trpc/server'
import { variantIDSearch, variantSimplifiedFormat } from '../nodes/variants'
import { commonHumanEdgeParamsFormat, variantsCommonQueryFormat } from '../params'
import { getSchema, getCollectionEnumValuesOrThrow } from '../schema'

const MAX_PAGE_SIZE = 100
const METHODS = getCollectionEnumValuesOrThrow('edges', 'variants_phenotypes', 'method')
const LABELS = getCollectionEnumValuesOrThrow('edges', 'variants_phenotypes', 'label')
const CLASS = getCollectionEnumValuesOrThrow('edges', 'variants_phenotypes', 'class')
const SOURCES = getCollectionEnumValuesOrThrow('edges', 'variants_phenotypes', 'source')

const variantsPhenotypesQueryFormat = z.object({
  phenotype_id: z.string().trim().optional(),
  log10pvalue: z.string().trim().optional(),
  method: z.enum(METHODS).optional(),
  label: z.enum(LABELS).optional(),
  class: z.enum(CLASS).optional()
})

const phenotypesVariantsInputFormat = z.object({
  phenotype_id: z.string().trim().optional(),
  phenotype_name: z.string().trim().optional(),
  log10pvalue: z.string().trim().optional(),
  method: z.enum(METHODS).optional(),
  label: z.enum(LABELS).optional(),
  class: z.enum(CLASS).optional(),
  files_fileset: z.string().optional(),
  source: z.enum(SOURCES).optional()
}).merge(commonHumanEdgeParamsFormat)

const gwasVariantPhenotypeFormat = z.object({
  rsid: z.array(z.string()).nullish(),
  phenotype_term: z.string().nullable(),
  study: z.string().or(studyFormat).optional(),
  log10pvalue: z.number().nullable(),
  p_val: z.number().nullable(),
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
  source_url: z.string().nullish(),
  class: z.string().nullish(),
  method: z.string().nullish(),
  label: z.string().nullish(),
  version: z.string().default('October 2022 (22.10)'),
  name: z.string(),
  variant: z.string().or(variantSimplifiedFormat)
})

const igvfVariantPhenotypeFormat = z.object({
  name: z.string(),
  source: z.string(),
  source_url: z.string(),
  score: z.number().nullable(),
  method: z.string().nullable(),
  class: z.string().nullish(),
  phenotype_term: z.string().nullable(),
  variant: z.string().or(variantSimplifiedFormat)
})

const variantPhenotypeFormat = gwasVariantPhenotypeFormat.or(igvfVariantPhenotypeFormat)

const variantToPhenotypeCollectionName = 'variants_phenotypes'
const studySchema = getSchema('data/schemas/nodes/studies.GWAS.json')
const studyCollectionName = studySchema.db_collection_name as string
const variantPhenotypeToStudy = getSchema('data/schemas/edges/variants_phenotypes_studies.GWAS.json')
const variantPhenotypeToStudyCollectionName = variantPhenotypeToStudy.db_collection_name as string

export function variantQueryValidation (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id', 'region', 'log10pvalue', 'files_fileset', 'method'].includes(item))

  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one variant property or log10pvalue or method or files_filesets must be defined.'
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

  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = ` AND record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
    delete input.files_fileset
  }

  let methodFilter = ''
  if (input.method !== undefined) {
    methodFilter = ` AND record.method == '${input.method as string}'`
    delete input.method
  }

  let classFilter = ''
  if (input.class !== undefined) {
    classFilter = ` AND record.class == '${input.class as string}'`
    delete input.class
  }

  let labelFilter = ''
  if (input.label !== undefined) {
    labelFilter = ` AND record.label == '${input.label as string}'`
    delete input.label
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

  const variantVerboseFields = '{_id: variant._key, chr: variant.chr, pos: variant.pos, alt: variant.alt, ref: variant.ref, rsid: variant.rsid, spdi: variant.spdi, hgvs: variant.hgvs, ca_id: variant.ca_id}'

  let query = ''

  let igvfQuery = `
      LET igvf = (
      FILTER record.source == 'IGVF'
      ${input.verbose === 'true' ? 'LET variant = DOCUMENT(record._from)' : ''}
      SORT record._key
      RETURN {
        name: record.name,
        source: record.source,
        source_url: record.source_url,
        score: record.score,
        method: record.method,
        class: record.class,
        phenotype_term: DOCUMENT(record._to).name,
        variant: ${input.verbose === 'true' ? variantVerboseFields : 'record._from'}
      }
    )
  `

  let gwasQuery = `
    LET gwas = (
      FOR edgeRecord IN ${variantPhenotypeToStudyCollectionName}
      FILTER edgeRecord._from == record._id ${pvalueFilter}
      ${input.verbose === 'true' ? 'LET variant = DOCUMENT(record._from)' : ''}
      SORT edgeRecord._key
      RETURN {
        'study': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'edgeRecord._to'},
        ${getDBReturnStatements(variantPhenotypeToStudy).replaceAll('record', 'edgeRecord')},
        'name': edgeRecord.inverse_name,
        'method': record.method,
        'label': record.label,
        'class': record.class,
        'source': record.source,
        'variant': ${input.verbose === 'true' ? variantVerboseFields : 'record._from'}
      }
    )
  `

  if (input.source === 'IGVF') {
    gwasQuery = 'LET gwas = []'
  } else if (input.source === 'OpenTargets') {
    igvfQuery = 'LET igvf = []'
  }

  if (input.phenotype_id !== undefined) {
    query = `
      FOR u in (
        FOR record IN ${variantToPhenotypeCollectionName}
          FILTER record._to == 'ontology_terms/${input.phenotype_id as string}' ${filesetFilter} ${methodFilter} ${classFilter} ${labelFilter}
          ${igvfQuery}
          ${gwasQuery}
          RETURN UNION(gwas, igvf)[0]
      )
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN u
  `
  } else {
    if (input.phenotype_name !== undefined) {
      query = `
      LET primaryTerms = (
        FOR record IN ontology_terms
        FILTER record.name == '${input.phenotype_name as string}'
        SORT record.name
        RETURN record._id
      )

      FOR u IN (
        FOR record IN ${variantToPhenotypeCollectionName}
          FILTER record._to IN primaryTerms ${filesetFilter} ${methodFilter} ${classFilter} ${labelFilter}
          ${gwasQuery}
          ${igvfQuery}
          RETURN UNION(gwas, igvf)[0]
      )
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN u
    `
    } else {
      let filters = [methodFilter.replace(' AND ', ''), classFilter.replace(' AND ', ''), labelFilter.replace(' AND ', '')].filter(item => item !== '').join(' AND ')
      if (filesetFilter !== '') {
        if (filters !== '') {
          filters += filesetFilter
        } else {
          filters += filesetFilter.replace(' AND ', '')
        }
      }

      if (filters === '') {
        throw new TRPCError({
          code: 'BAD_REQUEST',
          message: 'Either phenotype id, phenotype, method, or files_fileset must be defined.'
        })
      }

      // only IGVF records are queried for this case
      query = `
        FOR record IN ${variantToPhenotypeCollectionName}
          FILTER ${filters}
          SORT record._key
          ${input.verbose === 'true' ? 'LET variant = DOCUMENT(record._from)' : ''}
          LIMIT ${input.page as number * limit}, ${limit}
            RETURN {
              name: record.name,
              source: record.source,
              source_url: record.source_url,
              score: record.score,
              method: record.method,
              class: record.class,
              phenotype_term: DOCUMENT(record._to).name,
              variant: ${input.verbose === 'true' ? variantVerboseFields : 'record._from'}
            }
      `
    }
  }

  return await ((await db.query(query)).all())
}

async function findPhenotypesFromVariantSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  variantQueryValidation(input)
  delete input.organism

  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = `record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
    delete input.files_fileset
  }

  let variantIDs = []
  const hasVariantQuery = Object.keys(input).some(item => ['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id', 'region'].includes(item))
  if (hasVariantQuery) {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const variantInput: paramsFormatType = (({ variant_id, spdi, hgvs, ca_id, rsid, region }) => ({ variant_id, spdi, hgvs, ca_id, rsid, region }))(input)
    delete input.variant_id
    delete input.spdi
    delete input.hgvs
    delete input.rsid
    delete input.region
    delete input.ca_id
    variantIDs = await variantIDSearch(variantInput)
  }

  let phenotypeFilter = ''
  if (input.phenotype_id !== undefined) {
    phenotypeFilter = input.phenotype_id as string
    delete input.phenotype_id
  }

  let gwasHyperEdgeFilter = getHyperEdgeFilters(input)
  if (gwasHyperEdgeFilter !== '') {
    gwasHyperEdgeFilter = ` and ${gwasHyperEdgeFilter}`.replaceAll('record', 'edgeRecord')
  }

  const verboseQuery = `
    FOR targetRecord IN ${studyCollectionName}
      FILTER targetRecord._key == PARSE_IDENTIFIER(edgeRecord._to).key
      RETURN {${getDBReturnStatements(studySchema).replaceAll('record', 'targetRecord')}}
  `

  let igvfOnly = false
  let gwasOnly = false

  const queryFilter = []
  if (hasVariantQuery) {
    queryFilter.push(`record._from IN ['${variantIDs.join('\', \'')}']`)
  }

  if (phenotypeFilter !== '') {
    queryFilter.push(`record._to == 'ontology_terms/${phenotypeFilter}'`)
  }

  if (input.method !== undefined) {
    if (input.method !== 'GWAS') {
      igvfOnly = true
    } else {
      gwasOnly = true
    }
    queryFilter.push(`record.method == '${input.method as string}'`)
  }

  if (input.class !== undefined) {
    queryFilter.push(`record.class == '${input.class as string}'`)
  }

  if (input.label !== undefined) {
    if (input.label === 'GWAS') {
      gwasOnly = true
    } else {
      igvfOnly = true
    }
    queryFilter.push(`record.label == '${input.label as string}'`)
  }

  if (filesetFilter !== '') {
    queryFilter.push(filesetFilter)
    igvfOnly = true
  }

  const variantVerboseFields = '{_id: variant._key, chr: variant.chr, pos: variant.pos, alt: variant.alt, ref: variant.ref, rsid: variant.rsid, spdi: variant.spdi, hgvs: variant.hgvs, ca_id: variant.ca_id}'

  const singleIGVFQuery = `
    FOR record IN ${variantToPhenotypeCollectionName}
        FILTER ${queryFilter.join(' AND ')} AND record.source == 'IGVF'
        ${input.verbose === 'true' ? 'LET variant = DOCUMENT(record._from)' : ''}
        SORT record._key
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN {
          name: record.name,
          source: record.source,
          source_url: record.source_url,
          score: record.score,
          method: record.method,
          class: record.class,
          phenotype_term: DOCUMENT(record._to).name,
          variant: ${input.verbose === 'true' ? variantVerboseFields : 'record._from'}
        }
  `

  const singleGWASQuery = `
  FOR record IN ${variantToPhenotypeCollectionName}
      FILTER ${queryFilter.join(' AND ')}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      FOR edgeRecord IN ${variantPhenotypeToStudyCollectionName}
        FILTER edgeRecord._from == record._id ${gwasHyperEdgeFilter}
        ${input.verbose === 'true' ? 'LET variant = DOCUMENT(record._from)' : ''}
        SORT edgeRecord._key
        RETURN {
          rsid: DOCUMENT(record._from).rsid,
          study: ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'edgeRecord._to'},
          ${getDBReturnStatements(variantPhenotypeToStudy).replaceAll('record', 'edgeRecord')},
          name: edgeRecord.name,
          method: record.method,
          label: record.label,
          class: record.class,
          variant: ${input.verbose === 'true' ? variantVerboseFields : 'record._from'}
        }
  `

  const combinedQuery = `
    FOR u IN (
      FOR record IN ${variantToPhenotypeCollectionName}
        FILTER ${queryFilter.join(' AND ')}

        LET gwas = (
          FOR edgeRecord IN ${variantPhenotypeToStudyCollectionName}
          FILTER edgeRecord._from == record._id ${gwasHyperEdgeFilter}
          ${input.verbose === 'true' ? 'LET variant = DOCUMENT(record._from)' : ''}
          SORT edgeRecord._key
          RETURN {
            rsid: DOCUMENT(record._from).rsid,
            study: ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'edgeRecord._to'},
            ${getDBReturnStatements(variantPhenotypeToStudy).replaceAll('record', 'edgeRecord')},
            name: edgeRecord.name,
            method: record.method,
            label: record.label,
            class: record.class,
            variant: ${input.verbose === 'true' ? variantVerboseFields : 'record._from'}
          }
        )

        LET igvf = (
          FILTER record.source == 'IGVF'
          SORT record._key
          ${input.verbose === 'true' ? 'LET variant = DOCUMENT(record._from)' : ''}
          RETURN {
            name: record.name,
            source: record.source,
            source_url: record.source_url,
            score: record.score,
            method: record.method,
            class: record.class,
            phenotype_term: DOCUMENT(record._to).name,
            variant: ${input.verbose === 'true' ? variantVerboseFields : 'record._from'}
          }
        )

        RETURN UNION(gwas, igvf)[0]
    )
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN u
  `

  let query = combinedQuery
  if (igvfOnly) {
    query = singleIGVFQuery
  } else if (gwasOnly) {
    query = singleGWASQuery
  }

  return await ((await db.query(query)).all())
}

const variantsFromPhenotypes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/phenotypes/variants', description: descriptions.phenotypes_variants } })
  .input(phenotypesVariantsInputFormat)
  .output(z.array(variantPhenotypeFormat))
  .query(async ({ input }) => await findVariantsFromPhenotypesSearch(input))

const phenotypesFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/phenotypes', description: descriptions.variants_phenotypes } })
  .input(variantsCommonQueryFormat.merge(variantsPhenotypesQueryFormat).merge(commonHumanEdgeParamsFormat).merge(z.object({ files_fileset: z.string().optional() })))
  .output(z.array(variantPhenotypeFormat))
  .query(async ({ input }) => await findPhenotypesFromVariantSearch(input))

export const variantsPhenotypesRouters = {
  variantsFromPhenotypes,
  phenotypesFromVariants
}
