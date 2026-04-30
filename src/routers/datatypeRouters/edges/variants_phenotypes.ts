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
  phenotype_id: z.string().nullable(),
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
  biological_context: z.string().nullish(),
  source: z.string(),
  source_url: z.string(),
  score: z.number().nullable(),
  method: z.string().nullable(),
  class: z.string().nullish(),
  files_filesets: z.string().nullable(),
  phenotype_term: z.string().nullable(),
  variant: z.string().or(variantSimplifiedFormat),
  phenotype_id: z.string().nullable()
})

const variantPhenotypeFormat = gwasVariantPhenotypeFormat.or(igvfVariantPhenotypeFormat)

const variantVerboseFields = '{_id: variant._key, chr: variant.chr, pos: variant.pos, alt: variant.alt, ref: variant.ref, rsid: variant.rsid, spdi: variant.spdi, hgvs: variant.hgvs, ca_id: variant.ca_id}'

const variantToPhenotypeCollectionName = 'variants_phenotypes'
const studySchema = getSchema('data/schemas/nodes/studies.GWAS.json')
const studyCollectionName = studySchema.db_collection_name as string
const variantPhenotypeGwasSchema = getSchema('data/schemas/edges/variants_phenotypes.GWAS.json')
const variantsPhenotypeNonGwasSchema = getSchema('data/schemas/edges/variants_phenotypes.cV2F.json')

export function variantQueryValidation (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id', 'region', 'files_fileset', 'method'].includes(item))

  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one variant property, or method, or files_filesets must be defined.'
    })
  }
}

function phenotypeQueryValidation (input: paramsFormatType): void {
  const validKeys = ['phenotype_id', 'phenotype_name', 'method', 'files_fileset'] as const
  const definedKeysCount = validKeys.filter(key => key in input && input[key] !== undefined).length
  if (definedKeysCount < 1) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one phenotype property, or method, or files_filesets must be defined.'
    })
  }
}

function buildCombinedFilter (phenotypeFilter: string, nonGWASFilter: string, GWASFilter: string): string {
  return [phenotypeFilter, nonGWASFilter, GWASFilter].filter((filter) => filter !== '').join(' AND ') || 'true'
}

async function findVariantsFromPhenotypesSearch (input: paramsFormatType): Promise<any[]> {
  phenotypeQueryValidation(input)
  delete input.organism
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  if (input.files_fileset !== undefined) {
    input.files_filesets = `files_filesets/${input.files_fileset as string}`
    delete input.files_fileset
  }

  const nonGwasFilterInput: paramsFormatType = { method: input.method, class: input.class, label: input.label, files_filesets: input.files_filesets, source: input.source }
  const nonGWASFilter = getFilterStatements(variantsPhenotypeNonGwasSchema, nonGwasFilterInput)
  let GWASFilter = ''
  if (input.log10pvalue !== undefined) {
    GWASFilter = `${getFilterStatements(variantPhenotypeGwasSchema, { log10pvalue: input.log10pvalue })}`
  }

  const studyVerboseQuery = `
    FOR targetRecord IN ${studyCollectionName}
      FILTER targetRecord._id == record.study
      RETURN {${getDBReturnStatements(studySchema).replaceAll('record', 'targetRecord')}}
  `

  let phenotypeIds = []
  if (input.phenotype_id !== undefined || input.phenotype_name !== undefined) {
    if (input.phenotype_id !== undefined) {
      phenotypeIds.push(`ontology_terms/${input.phenotype_id as string}`)
    } else {
      const phenotypeQuery = `
        FOR record IN ontology_terms
        FILTER record.name == '${input.phenotype_name as string}'
        RETURN record._id
      `
      phenotypeIds = await (await db.query(phenotypeQuery)).all()
    }
  }
  const phenotypeFilter = phenotypeIds.length > 0 ? 'record._to IN @phenotypeIds' : ''

  const query = `
  FOR record IN ${variantToPhenotypeCollectionName}
    FILTER ${buildCombinedFilter(phenotypeFilter, nonGWASFilter, GWASFilter)}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}

    ${input.verbose === 'true' ? 'LET variant = DOCUMENT(record._from)' : ''}
    LET phenotype_name = DOCUMENT(record._to).name
    RETURN {
      variant:      ${input.verbose === 'true' ? variantVerboseFields : 'record._from'},
      phenotype_id: record._to,
      name:         record.name,
      source:       record.source,
      source_url:   record.source_url,
      class:        record.class,
      method:       record.method,
      label:        record.label,
      phenotype_term: phenotype_name,

      // OpenTargets-specific
      version:        record.source == 'OpenTargets' ? record.version        : null,
      lead_chrom:     record.source == 'OpenTargets' ? record.lead_chrom     : null,
      lead_pos:       record.source == 'OpenTargets' ? record.lead_pos       : null,
      lead_ref:       record.source == 'OpenTargets' ? record.lead_ref       : null,
      lead_alt:       record.source == 'OpenTargets' ? record.lead_alt       : null,
      direction:      record.source == 'OpenTargets' ? record.direction      : null,
      beta:           record.source == 'OpenTargets' ? record.beta           : null,
      beta_ci_lower:  record.source == 'OpenTargets' ? record.beta_ci_lower  : null,
      beta_ci_upper:  record.source == 'OpenTargets' ? record.beta_ci_upper  : null,
      p_val_mantissa: record.source == 'OpenTargets' ? record.p_val_mantissa : null,
      p_val_exponent: record.source == 'OpenTargets' ? record.p_val_exponent : null,
      p_val:          record.source == 'OpenTargets' ? record.p_val          : null,
      log10pvalue:    record.source == 'OpenTargets' ? record.log10pvalue    : null,
      oddsr_ci_lower: record.source == 'OpenTargets' ? record.oddsr_ci_lower : null,
      oddsr_ci_upper: record.source == 'OpenTargets' ? record.oddsr_ci_upper : null,
      study:          record.source == 'OpenTargets' ? ${input.verbose === 'true' ? `(${studyVerboseQuery})[0]` : 'record.study'} : null,

      // non-OpenTargets specific
      score:              record.source != 'OpenTargets' ? record.score              : null,
      files_filesets:     record.source != 'OpenTargets' ? record.files_filesets     : null,
      biosample_term:     record.source != 'OpenTargets' ? record.biosample_term     : null,
      biological_context: record.source != 'OpenTargets' ? record.biological_context : null
    }
  `

  let result = []
  if (phenotypeIds.length > 0) {
    result = await ((await db.query(query, { phenotypeIds })).all())
  } else {
    result = await ((await db.query(query)).all())
  }
  return result
}

async function findPhenotypesFromVariantSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  variantQueryValidation(input)
  delete input.organism

  if (input.files_fileset !== undefined) {
    input.files_filesets = `files_filesets/${input.files_fileset as string}`
    delete input.files_fileset
  }

  if (input.phenotype_id !== undefined) {
    input.phenotype_id = `ontology_terms/${input.phenotype_id as string}`
  }
  const nonGwasFilterInput: paramsFormatType = { method: input.method, class: input.class, label: input.label, files_filesets: input.files_filesets, source: input.source, _to: input.phenotype_id }
  const nonGWASFilter = getFilterStatements(variantsPhenotypeNonGwasSchema, nonGwasFilterInput)
  let GWASFilter = ''
  if (input.log10pvalue !== undefined) {
    GWASFilter = `${getFilterStatements(variantPhenotypeGwasSchema, { log10pvalue: input.log10pvalue })}`
  }

  const studyVerboseQuery = `
    FOR targetRecord IN ${studyCollectionName}
      FILTER targetRecord._id == record.study
      RETURN {${getDBReturnStatements(studySchema).replaceAll('record', 'targetRecord')}}
  `
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
  const variantFilter = hasVariantQuery ? 'record._from IN @variantIDs' : ''
  const combinedFilter = buildCombinedFilter(variantFilter, nonGWASFilter, GWASFilter)
  const query = `
    FOR record IN ${variantToPhenotypeCollectionName}
    FILTER ${combinedFilter}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    ${input.verbose === 'true' ? 'LET variant = DOCUMENT(record._from)' : ''}
    RETURN MERGE(
      {
        variant: ${input.verbose === 'true' ? variantVerboseFields : 'record._from'},
        phenotype_id: record._to,
      },

        (record.source == 'OpenTargets' ? {
          study: ${input.verbose === 'true' ? `(${studyVerboseQuery})[0]` : 'record.study'},
          ${getDBReturnStatements(variantPhenotypeGwasSchema).replaceAll('record', 'record')}
        } : {
          ${getDBReturnStatements(variantsPhenotypeNonGwasSchema).replaceAll('record', 'record')},
          phenotype_term: DOCUMENT(record._to).name
        })
    )
  `
  console.log(query)
  let result = []
  if (hasVariantQuery) {
    result = await ((await db.query(query, { variantIDs })).all())
  } else {
    result = await ((await db.query(query)).all())
  }
  return result
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
