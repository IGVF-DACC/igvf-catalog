import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { ontologyFormat } from '../nodes/ontologies'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { variantIDSearch, variantSimplifiedFormat } from '../nodes/variants'
import { proteinByIDQuery, proteinFormat } from '../nodes/proteins'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { z } from 'zod'
import { commonHumanEdgeParamsFormat, proteinsCommonQueryFormat, variantsCommonQueryFormat } from '../params'
import { complexFormat } from '../nodes/complexes'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 100
const METHODS = ['ADASTRA', 'GVATdb', 'pQTL', 'SEMVAR'] as const
const LABELS = ['allele-specific binding', 'pQTL', 'predicted allele-specific binding'] as const
const SOURCES = ['ADASTRA', 'GVATdb', 'IGVF', 'UKB'] as const

const asbSchema = getSchema('data/schemas/edges/variants_proteins.ASB.json')
const ukbSchema = getSchema('data/schemas/edges/variants_proteins.pQTL.json')
const semplSchema = getSchema('data/schemas/edges/variants_proteins.SEMPred.json')
const gvatdbSchema = getSchema('data/schemas/edges/variants_proteins.ASB_GVATDB.json')
const proteinSchema = getSchema('data/schemas/nodes/proteins.GencodeProtein.json')
const variantsProteinsDatabaseName = asbSchema.db_collection_name as string
const proteinCollectionName = proteinSchema.db_collection_name as string
const complexesProteinsCollectionName = 'complexes_proteins'

const variantsProteinsQueryFormat = z.object({
  label: z.enum(LABELS).optional(),
  source: z.enum(SOURCES).optional(),
  method: z.enum(METHODS).optional(),
  files_fileset: z.string().optional(),
  name: z.enum(['modulates binding of', 'associated with levels of']).optional()
})

const proteinsQuery = proteinsCommonQueryFormat.merge(variantsProteinsQueryFormat).merge(commonHumanEdgeParamsFormat).merge(z.object({
  name: z.enum(['binding modulated by', 'level associated with']).optional(),
  method: z.enum(METHODS).optional()
}))

const variantsQuery = variantsCommonQueryFormat
  .merge(variantsProteinsQueryFormat)
  .merge(commonHumanEdgeParamsFormat)

const outputFormat = z.object({
  sequence_variant: z.string().or(variantSimplifiedFormat).optional(),
  protein_complex: z.string().or(proteinFormat.omit({ dbxrefs: true })).or(complexFormat).optional(),
  biosample_term: z.string().or(ontologyFormat).nullish(),
  biological_context: z.string().nullish(),
  regulatory_type: z.string().nullish(),
  class: z.string().nullish(),
  label: z.string().nullish(),
  name: z.string(),
  method: z.string().nullish(),
  files_filesets: z.string().nullish(),
  source: z.string().nullish(),
  source_url: z.string().nullish(),
  is_complex: z.boolean(),
  score: z.number().nullish(),
  fdrp_bh_ref: z.string().nullish(),
  fdrp_bh_alt: z.string().nullish(),
  motif: z.string().nullish(),
  motif_fc: z.string().nullish(),
  beta: z.number().nullish(),
  se: z.number().nullish(),
  gene: z.string().nullish(),
  gene_consequence: z.string().nullish(),
  log10pvalue: z.number().nullish(),
  p_value: z.number().nullish(),
  fdr: z.number().nullish(),
  variant_effect_score: z.number().nullish(),
  SEMpl_annotation: z.string().nullish(),
  SEMpl_baseline: z.number().nullish(),
  alt_score: z.number().nullish(),
  ref_score: z.number().nullish(),
  relative_binding_affinity: z.number().nullish(),
  effect_on_binding: z.string().nullish()
})

const ADASTRA_SCORE_EXPR = `(
  TO_NUMBER(record.fdrp_bh_ref) < 0.05 && TO_NUMBER(record.fdrp_bh_alt) < 0.05
    ? null
    : (
      TO_NUMBER(record.fdrp_bh_ref) < 0.05
        ? -TO_NUMBER(record.fdrp_bh_ref)
        : (TO_NUMBER(record.fdrp_bh_alt) < 0.05 ? TO_NUMBER(record.fdrp_bh_alt) : null)
    )
)`

const buildEdgeFilter = (input: paramsFormatType, nameField: 'name' | 'inverse_name'): string => {
  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = `record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
    delete input.files_fileset
  }

  let methodFilter = ''
  let sourceFilter = ''
  if (input.method !== undefined) {
    methodFilter = `record.method == '${input.method as string}'`
    delete input.method
  }

  if (input.source !== undefined) {
    sourceFilter = `record.source == '${input.source as string}'`
    delete input.source
  }

  let labelFilter = ''
  if (input.label !== undefined) {
    labelFilter = `record.label == '${input.label as string}'`
    delete input.label
  }

  let nameFilter = ''
  if (input.name !== undefined) {
    nameFilter = `record.${nameField} == '${input.name as string}'`
    delete input.name
  }

  return [methodFilter, labelFilter, nameFilter, filesetFilter, sourceFilter]
    .filter((filter) => filter !== '')
    .join(' AND ')
}

const buildCombinedFilter = (primaryFilter: string, edgeFilter: string): string => {
  return [primaryFilter, edgeFilter].filter((filter) => filter !== '').join(' AND ') || 'true'
}

const buildQuery = ({
  combinedFilter,
  limit,
  page,
  verbose,
  nameField
}: {
  combinedFilter: string
  limit: number
  page: number
  verbose: boolean
  nameField: 'name' | 'inverse_name'
}): string => `

  // 1. Fetch the primary edge records
  LET initialEdges = (
    FOR record in ${variantsProteinsDatabaseName}
      FILTER ${combinedFilter}
      SORT record._key
      LIMIT ${page * limit}, ${limit}
      RETURN record
  )

  // 2. Collect all unique IDs for batch fetching
  LET variantIds = UNIQUE(initialEdges[*]._from)
  LET proteinComplexIds  = UNIQUE(initialEdges[*]._to)
  LET ontologyIds = UNIQUE(initialEdges[* FILTER CURRENT.biosample_term != null].biosample_term)

  // 3. Batch fetch Documents into Lookups (Only if verbose is requested)
  LET variantLookup = ${verbose
  ? `(
    FOR v IN variants
      FILTER v._id IN variantIds
      RETURN { [v._id]: v }
  )`
  : '[]'}

  // Multi-collection target lookup
  LET proteinComplexLookup = ${verbose
  ? `(
    FOR t IN UNION(
      (FOR p IN proteins FILTER p._id IN proteinComplexIds RETURN p),
      (FOR c IN complexes FILTER c._id IN proteinComplexIds RETURN c)
    )
    RETURN { [t._id]: t }
  )`
  : '[]'}

  LET ontologyLookup = ${verbose
  ? `(
    FOR o IN ontology_terms
      FILTER o._id IN ontologyIds
      RETURN { [o._id]: o }
  )`
  : '[]'}

  // 4. Flatten the lookups into single objects for O(1) access
  LET vMap = MERGE(variantLookup)
  LET tMap = MERGE(proteinComplexLookup)
  LET oMap = MERGE(ontologyLookup)

  // 5. Transform and Return
  FOR record in initialEdges
    // Resolve variant, protein_complex and ontology term
    LET variant = ${verbose ? 'vMap[record._from]' : 'record._from'}
    LET proteinComplex  = ${verbose ? 'tMap[record._to]' : 'record._to'}
    LET bioTerm = ${verbose ? 'oMap[record.biosample_term]' : 'record.biosample_term'}

    // Check if the _to ID starts with the 'complexes' collection name
    LET is_complex = CONTAINS(record._to, "complexes/")

    LET base = {
      'sequence_variant': variant,
      'protein_complex': proteinComplex,
      'name': record.${nameField},
      'is_complex': is_complex
    }

    // Append source-specific metadata
    RETURN MERGE(base,
      record.source == 'ADASTRA' ? {
        'biosample_term': bioTerm,
        'score': ${ADASTRA_SCORE_EXPR},
        'method': record.method,
        ${getDBReturnStatements(asbSchema)}
      } :
      record.source == 'GVATdb' ? {
        'method': record.method,
        ${getDBReturnStatements(gvatdbSchema)}
      } :
      record.source == 'UKB' ? {
        'method': record.method,
        ${getDBReturnStatements(ukbSchema)}
      } :
      record.source == 'IGVF' ? {
        'biosample_term': bioTerm,
        ${getDBReturnStatements(semplSchema)}
      } : {}
    )
`

function variantQueryValidation (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id', 'region', 'method', 'files_fileset'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one variant property or method or files_fileset must be defined.'
    })
  }
}

function proteinQueryValidation (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['protein_id', 'protein_name', 'uniprot_name', 'uniprot_full_name', 'dbxrefs', 'method', 'files_fileset'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one protein property or method or files_fileset must be defined.'
    })
  }
}

async function variantsFromProteinSearch (input: paramsFormatType): Promise<any[]> {
  proteinQueryValidation(input)
  delete input.organism
  const verbose = input.verbose === 'true'
  delete input.verbose

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  let proteinComplexIDs: string[] = []
  const isProteinQuery = Object.keys(input).some(item => ['protein_id', 'protein_name', 'uniprot_name', 'uniprot_full_name', 'dbxrefs'].includes(item))
  if (isProteinQuery) {
    let proteinQuery = ''
    if (input.protein_id !== undefined) {
      proteinQuery = proteinByIDQuery(input.protein_id as string)
    } else {
      // eslint-disable-next-line @typescript-eslint/naming-convention
      const proteinInput: paramsFormatType = (({ protein_name, uniprot_name, uniprot_full_name, dbxrefs }) => ({ name: protein_name, uniprot_names: uniprot_name, uniprot_full_names: uniprot_full_name, dbxrefs }))(input)
      const filtersForProteinSearch = getFilterStatements(proteinSchema, proteinInput)
      proteinQuery = `
        FOR record IN ${proteinCollectionName}
        FILTER ${filtersForProteinSearch}
        RETURN record._id
      `
    }
    delete input.protein_id
    delete input.protein_name
    delete input.uniprot_name
    delete input.uniprot_full_name
    const proteinComplexQuery = `
      LET proteinIds = (${proteinQuery})

      LET complexIds = (
          FOR record IN ${complexesProteinsCollectionName as string}
          FILTER record._to IN proteinIds
          SORT record._key
          RETURN record._from
        )
      RETURN APPEND(proteinIds, complexIds)
    `
    proteinComplexIDs = (await (await db.query(proteinComplexQuery)).all())[0]
  }

  const edgeFilter = buildEdgeFilter(input, 'inverse_name')
  const proteinFilter = isProteinQuery ? 'record._to IN @proteinComplexIDs' : ''
  const combinedFilter = buildCombinedFilter(proteinFilter, edgeFilter)

  const query = buildQuery({
    combinedFilter,
    limit,
    page: input.page as number,
    verbose,
    nameField: 'inverse_name'
  })
  let result: any[] = []
  if (isProteinQuery) {
    result = await (await db.query(query, { proteinComplexIDs })).all()
  } else {
    result = await (await db.query(query)).all()
  }
  return result
}

async function proteinsFromVariantSearch (input: paramsFormatType): Promise<any[]> {
  variantQueryValidation(input)
  delete input.organism
  const verbose = input.verbose === 'true'
  delete input.verbose

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  let variantIDs: string[] = []
  // check if variant properties are defined
  const isVariantQuery = Object.keys(input).some(item => ['variant_id', 'spdi', 'hgvs', 'rsid', 'ca_id', 'region'].includes(item))
  if (isVariantQuery) {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const variantInput: paramsFormatType = (({ variant_id, spdi, hgvs, ca_id, rsid, region }) => ({ variant_id, spdi, hgvs, ca_id, rsid, region }))(input)
    delete input.variant_id
    delete input.spdi
    delete input.hgvs
    delete input.rsid
    delete input.ca_id
    delete input.region
    variantIDs = await variantIDSearch(variantInput)
  }
  const edgeFilter = buildEdgeFilter(input, 'name')
  const variantFilter = isVariantQuery ? 'record._from IN @variantIDs' : ''
  const combinedFilter = buildCombinedFilter(variantFilter, edgeFilter)
  const query = buildQuery({
    combinedFilter,
    limit,
    page: input.page as number,
    verbose,
    nameField: 'name'
  })
  let result: any[] = []
  if (isVariantQuery) {
    result = await (await db.query(query, { variantIDs })).all()
  } else {
    result = await (await db.query(query)).all()
  }
  return result
}

const variantsFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/variants', description: descriptions.proteins_variants } })
  .input(proteinsQuery)
  .output(z.array(outputFormat))
  .query(async ({ input }) => await variantsFromProteinSearch(input))

const proteinsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/proteins', description: descriptions.variants_proteins } })
  .input(variantsQuery)
  .output(z.array(outputFormat))
  .query(async ({ input }) => await proteinsFromVariantSearch(input))

export const variantsProteinsRouters = {
  proteinsFromVariants,
  variantsFromProteins
}
