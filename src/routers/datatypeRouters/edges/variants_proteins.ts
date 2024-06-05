import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { ontologyFormat } from '../nodes/ontologies'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { variantSimplifiedFormat, variantsQueryFormat } from '../nodes/variants'
import { proteinFormat, proteinsQueryFormat } from '../nodes/proteins'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'

const MAX_PAGE_SIZE = 100

const schema = loadSchemaConfig()

// primary: variants -> proteins (generic context)
const asbSchema = schema['allele specific binding']
const ukbSchema = schema['variant to protein association']
const variantSchema = schema['sequence variant']
const proteinSchema = schema.protein

// secondary: variants -> (edge) proteins, (edge) -> biosample terms (cell-type specific context)
// asb -> ontology term
const asbCOSchema = schema['allele specific binding cell ontology']
const ontologyTermSchema = schema['ontology term']

const variantsProteinsDatabaseName = asbSchema.db_collection_name as string

const sourceValues = z.enum([
  'ADASTRA allele-specific TF binding calls',
  'GVATdb allele-specific TF binding calls',
  'UKB'
])
const typeValues = z.enum([
  'allele-specific binding',
  'pQTL'
])

const AsbQueryFormat = z.object({
  type: typeValues.optional(),
  source: sourceValues.optional(),
  verbose: z.enum(['true', 'false']).default('false'),
  page: z.number().default(0)

})

const AsbFormat = z.object({
  'sequence variant': z.string().or(variantSimplifiedFormat).optional(),
  protein: z.string().or(proteinFormat.omit({ dbxrefs: true })).optional(),
  'ontology term': z.string().or(ontologyFormat).optional(),
  biological_context: z.string().nullish(),
  es_mean_ref: z.string().nullish(),
  es_mean_alt: z.string().nullish(),
  fdrp_bh_ref: z.string().nullish(),
  fdrp_bh_alt: z.string().nullish(),
  motif_fc: z.string().nullish(),
  motif_pos: z.string().nullish(),
  motif_orient: z.string().nullish(),
  motif_conc: z.string().nullish(),
  motif: z.string().nullish(),
  source: z.string().nullish(),
  beta: z.number().nullish(),
  se: z.number().nullish(),
  class: z.string().nullish(),
  gene: z.string().nullish(),
  gene_consequence: z.string().nullish(),
  type: z.string().nullish(),
  log10pvalue: z.number().nullish(),
  p_value: z.number().nullish(),
  hg19_coordinate: z.string().nullish()

})
const variantVerboseQuery = `
    FOR otherRecord IN ${variantSchema.db_collection_name as string}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
      RETURN {${getDBReturnStatements(variantSchema).replaceAll('record', 'otherRecord')}}
  `
const proteinVerboseQuery = `
  FOR otherRecord IN ${proteinSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(proteinSchema).replaceAll('record', 'otherRecord')}}
  `

const ontologyTermVerboseQuery = `
  FOR targetRecord IN ${ontologyTermSchema.db_collection_name as string}
    FILTER targetRecord._key == PARSE_IDENTIFIER(edgeRecord._to).key
    RETURN {${getDBReturnStatements(ontologyTermSchema).replaceAll('record', 'targetRecord')}}
  `

async function variantsFromProteinSearch (input: paramsFormatType): Promise<any[]> {
  if (input.protein_id !== undefined) {
    input._id = `proteins/${input.protein_id as string}`
    delete input.protein_id
  }

  const verbose = input.verbose === 'true'
  delete input.verbose

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const variantsProteinsInput: paramsFormatType = {}
  if (input.source !== undefined) {
    variantsProteinsInput.source = input.source
    delete input.source
  }
  if (input.type !== undefined) {
    variantsProteinsInput.type = input.type
    delete input.type
  }

  let variantsProteinsFilter = getFilterStatements(asbSchema, variantsProteinsInput)
  if (variantsProteinsFilter) {
    variantsProteinsFilter = ` AND ${variantsProteinsFilter}`
  }

  const filterForProteinSearch = getFilterStatements(proteinSchema, input)
  if (filterForProteinSearch === '') {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one protein property must be defined.'
    })
  }
  const query = `
    LET proteinIds = (
      FOR record IN ${proteinSchema.db_collection_name as string}
      FILTER ${filterForProteinSearch}
      RETURN record._id
    )
    LET variantsProteinsEdges = (
      FOR record in ${variantsProteinsDatabaseName}
        FILTER record._to IN proteinIds ${variantsProteinsFilter}
        SORT record._key
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN record
    )
    LET ADASTRA = (
      FOR record in variantsProteinsEdges
        FILTER record.source == 'ADASTRA allele-specific TF binding calls'
        RETURN (
          FOR edgeRecord IN ${asbCOSchema.db_collection_name as string}
          FILTER edgeRecord._from == record._id
          RETURN {
            'sequence variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
            'protein': ${verbose ? `(${proteinVerboseQuery})[0]` : 'record._to'},
            'ontology term': ${verbose ? `(${ontologyTermVerboseQuery})[0]` : 'edgeRecord._to'},
            'motif_fc': record['motif_fc'], 'motif_pos': record['motif_pos'], 'motif_orient': record['motif_orient'], 'motif_conc': record['motif_conc'], 'motif': record['motif'], 'source': record['source'],
            ${getDBReturnStatements(asbCOSchema).replaceAll('record', 'edgeRecord')}
          }
        )[0]
    )
    LET GVATdb = (
      FOR record in variantsProteinsEdges
        FILTER record.source == 'GVATdb allele-specific TF binding calls'
        RETURN {
          'sequence variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
          'protein': ${verbose ? `(${proteinVerboseQuery})[0]` : 'record._to'},
            'log10pvalue': record['log10pvalue:long'], 'p_value': record['p_value:long'], 'hg19_coordinate': record['hg19_coordinate'], 'source': record['source'], 'type': record['type']
          }
    )
    LET UKB = (
      FOR record in variantsProteinsEdges
        FILTER record.source == 'UKB'
        RETURN {
          'sequence variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
          'protein': ${verbose ? `(${proteinVerboseQuery})[0]` : 'record._to'},
            ${getDBReturnStatements(ukbSchema)}
          }
    )
    LET mergedArray = APPEND(ADASTRA, GVATdb)
    RETURN APPEND(mergedArray, UKB)
    `
  const result = (await (await db.query(query)).all()).filter((record) => record !== null)
  return result[0]
}

async function proteinsFromVariantSearch (input: paramsFormatType): Promise<any[]> {
  if (input.variant_id !== undefined) {
    input._id = `variants/${input.variant_id as string}`
    delete input.variant_id
  }

  const verbose = input.verbose === 'true'
  delete input.verbose

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const variantsProteinsInput: paramsFormatType = {}
  if (input.source !== undefined) {
    variantsProteinsInput.source = input.source
    delete input.source
  }
  if (input.type !== undefined) {
    variantsProteinsInput.type = input.type
    delete input.type
  }

  let variantsProteinsFilter = getFilterStatements(asbSchema, variantsProteinsInput)
  if (variantsProteinsFilter) {
    variantsProteinsFilter = ` AND ${variantsProteinsFilter}`
  }

  const filterForVariantSearch = getFilterStatements(variantSchema, input)
  if (filterForVariantSearch === '') {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one variant property must be defined.'
    })
  }
  const variantVerboseQuery = `
    FOR otherRecord IN ${variantSchema.db_collection_name as string}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
      RETURN {${getDBReturnStatements(variantSchema).replaceAll('record', 'otherRecord')}}
  `
  const query = `
    LET variantIds = (
      FOR record IN ${variantSchema.db_collection_name as string}
      FILTER ${filterForVariantSearch}
      RETURN record._id
    )
    LET variantsProteinsEdges = (
      FOR record in ${variantsProteinsDatabaseName}
        FILTER record._from IN variantIds ${variantsProteinsFilter}
        SORT record._key
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN record
    )
    LET ADASTRA = (
      FOR record in variantsProteinsEdges
        FILTER record.source == 'ADASTRA allele-specific TF binding calls'
        RETURN (
          FOR edgeRecord IN ${asbCOSchema.db_collection_name as string}
          FILTER edgeRecord._from == record._id
          RETURN {
            'sequence variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
            'protein': ${verbose ? `(${proteinVerboseQuery})[0]` : 'record._to'},
            'ontology term': ${verbose ? `(${ontologyTermVerboseQuery})[0]` : 'edgeRecord._to'},
            'motif_fc': record['motif_fc'], 'motif_pos': record['motif_pos'], 'motif_orient': record['motif_orient'], 'motif_conc': record['motif_conc'], 'motif': record['motif'], 'source': record['source'],
            ${getDBReturnStatements(asbCOSchema).replaceAll('record', 'edgeRecord')}
          }
        )[0]
    )
    LET GVATdb = (
      FOR record in variantsProteinsEdges
        FILTER record.source == 'GVATdb allele-specific TF binding calls'
        RETURN {
          'sequence variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
          'protein': ${verbose ? `(${proteinVerboseQuery})[0]` : 'record._to'},
            'log10pvalue': record['log10pvalue:long'], 'p_value': record['p_value:long'], 'hg19_coordinate': record['hg19_coordinate'], 'source': record['source'], 'type': record['type']
          }
    )
    LET UKB =(
      FOR record in variantsProteinsEdges
        FILTER record.source == 'UKB'
        RETURN {
          'sequence variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
          'protein': ${verbose ? `(${proteinVerboseQuery})[0]` : 'record._to'},
            ${getDBReturnStatements(ukbSchema)}
          }
    )
    LET mergedArray = APPEND(ADASTRA, GVATdb)
    RETURN APPEND(mergedArray, UKB)
    `
  const result = (await (await db.query(query)).all()).filter((record) => record !== null)
  return result[0]
}

const proteinsQuery = proteinsQueryFormat.merge(
  z.object({ limit: z.number().optional() })
).omit({
  organism: true,
  name: true
}).merge(AsbQueryFormat).merge(z.object({ protein_name: z.string().optional() })).transform(({ protein_name, ...rest }) => ({
  name: protein_name,
  ...rest
}))

// Only keep cell-type scpecific queries for ASB endpoints here
// /variants/proteins, /proteins/variants -> returns cell-type specific values from hyperedges & generic values from primary edges (motif-relevant values)
const variantsFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/variants', description: descriptions.proteins_variants } })
  .input(proteinsQuery)
  .output(z.array(AsbFormat))
  .query(async ({ input }) => await variantsFromProteinSearch(input))

const proteinsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/proteins', description: descriptions.variants_proteins } })
  .input(variantsQueryFormat.omit({ organism: true, mouse_strain: true, region: true, funseq_description: true }).merge(AsbQueryFormat).merge(z.object({ limit: z.number().optional() })))
  .output(z.array(AsbFormat))
  .query(async ({ input }) => await proteinsFromVariantSearch(input))

export const variantsProteinsRouters = {
  proteinsFromVariants,
  variantsFromProteins
}
