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
// primary: variants -> proteins (generic context)
const asbSchema = getSchema('data/schemas/edges/variants_proteins.ASB.json')
const variantsProteinsDatabaseName = (asbSchema.accessible_via as Record<string, any>).name as string
const ukbSchema = getSchema('data/schemas/edges/variants_proteins.pQTL.json')
const semplSchema = getSchema('data/schemas/edges/variants_proteins.SEMPred.json')
const variantSchema = getSchema('data/schemas/nodes/variants.Favor.json')
const variantCollectionName = (variantSchema.accessible_via as Record<string, any>).name as string
const proteinSchema = getSchema('data/schemas/nodes/proteins.GencodeProtein.json')
const proteinCollectionName = (proteinSchema.accessible_via as Record<string, any>).name as string
const complexSchema = getSchema('data/schemas/nodes/complexes.EBIComplex.json')
const complexCollectionName = (complexSchema.accessible_via as Record<string, any>).name as string
const complexesProteinsCollectionName = 'complexes_proteins'

// secondary: variants -> (edge) proteins, (edge) -> biosample terms (cell-type specific context)
// asb -> ontology term
const asbCOSchema = getSchema('data/schemas/edges/variants_proteins_terms.ASB.json')
const ontologyTermSchema = getSchema('data/schemas/nodes/ontology_terms.Ontology.json')
const ontologyTermCollectionName = (ontologyTermSchema.accessible_via as Record<string, any>).name as string

const sourceValues = z.enum([
  'ADASTRA allele-specific TF binding calls',
  'GVATdb allele-specific TF binding calls',
  'IGVF',
  'UKB'
])
const labelValues = z.enum([
  'allele-specific binding',
  'pQTL',
  'predicted allele specific binding'
])

const variantsProteinsQueryFormat = z.object({
  label: labelValues.optional(),
  source: sourceValues.optional(),
  name: z.enum(['modulates binding of', 'associated with levels of']).optional()
})

const proteinsQuery = proteinsCommonQueryFormat.merge(variantsProteinsQueryFormat).merge(commonHumanEdgeParamsFormat).merge(z.object({
  name: z.enum(['binding modulated by', 'level associated with']).optional()
}))

const variantsQuery = variantsCommonQueryFormat.merge(variantsProteinsQueryFormat).merge(commonHumanEdgeParamsFormat)

const AsbFormat = z.object({
  sequence_variant: z.string().or(variantSimplifiedFormat).optional(),
  protein: z.string().or(proteinFormat.omit({ dbxrefs: true })).optional(),
  complex: z.string().or(complexFormat).optional(),
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
  label: z.string().nullish(),
  log10pvalue: z.number().nullish(),
  p_value: z.number().nullish(),
  hg19_coordinate: z.string().nullish(),
  variant_effect_score: z.number().nullish(),
  SEMpl_annotation: z.string().nullish(),
  SEMpl_baseline: z.number().nullish(),
  alt_score: z.number().nullish(),
  ref_score: z.number().nullish(),
  relative_binding_affinity: z.number().nullish(),
  effect_on_binding: z.string().nullish(),
  name: z.string(),
  score: z.array(z.object({
    biological_context: z.string().nullish(),
    fdrp_bh_ref: z.string().nullish()
  })).nullish()
})

const variantVerboseQuery = `
    FOR otherRecord IN ${variantCollectionName}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
      RETURN {${getDBReturnStatements(variantSchema).replaceAll('record', 'otherRecord')}}
  `
const proteinVerboseQuery = `
  FOR otherRecord IN ${proteinCollectionName}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(proteinSchema).replaceAll('record', 'otherRecord')}}
  `

const complexVerboseQuery = `
  FOR otherRecord IN ${complexCollectionName}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(complexSchema).replaceAll('record', 'otherRecord')}}
  `

const ontologyTermVerboseQuery = `
  FOR targetRecord IN ${ontologyTermCollectionName}
    FILTER targetRecord._key == PARSE_IDENTIFIER(edgeRecord._to).key
    RETURN {${getDBReturnStatements(ontologyTermSchema).replaceAll('record', 'targetRecord')}}
  `
export function variantQueryValidation (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['variant_id', 'spdi', 'hgvs', 'rsid', 'chr', 'position'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one variant property must be defined.'
    })
  }
  if ((input.chr === undefined && input.position !== undefined) || (input.chr !== undefined && input.position === undefined)) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Chromosome and position must be defined together.'
    })
  }
}
async function variantsFromProteinSearch (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  const verbose = input.verbose === 'true'
  delete input.verbose

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let nameFilters = ''
  if (input.name !== undefined) {
    nameFilters += ` AND record.inverse_name == '${input.name as string}'`
    delete input.name
  }

  const variantsProteinsInput: paramsFormatType = {}
  if (input.source !== undefined) {
    variantsProteinsInput.source = input.source
    delete input.source
  }
  if (input.label !== undefined) {
    variantsProteinsInput.label = input.label
    delete input.label
  }

  let proteinQuery
  if (input.protein_id !== undefined) {
    proteinQuery = proteinByIDQuery(input.protein_id as string)
  } else {
    input.names = input.protein_name
    input.full_names = input.full_name
    delete input.protein_name
    delete input.full_name

    const filterForProteinSearch = getFilterStatements(proteinSchema, input)
    if (filterForProteinSearch === '') {
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: 'At least one protein property must be defined.'
      })
    }

    proteinQuery = `(
        FOR record IN ${proteinCollectionName}
        FILTER ${filterForProteinSearch}
        RETURN record._id
      )
    `
  }

  let variantsProteinsFilter = getFilterStatements(asbSchema, variantsProteinsInput)
  if (variantsProteinsFilter) {
    variantsProteinsFilter = ` AND ${variantsProteinsFilter}`
  }

  const query = `
    LET proteinIds = ${proteinQuery}

    LET complexIds = (
        FOR record IN ${complexesProteinsCollectionName as string}
        FILTER record._to IN proteinIds
        SORT record._key
        RETURN record._from
      )
    LET toIds = APPEND(proteinIds, complexIds)

    LET variantsProteinsEdges = (
      FOR record in ${variantsProteinsDatabaseName}
        FILTER record._to IN toIds ${variantsProteinsFilter} ${nameFilters}
        SORT record._key
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN record
    )
    LET ADASTRA = (
      FOR record in variantsProteinsEdges
        FILTER record.source == 'ADASTRA allele-specific TF binding calls'
        RETURN (
          FOR edgeRecord IN ${variantsProteinsDatabaseName}
          FILTER edgeRecord._from == record._id
          RETURN {
            'sequence_variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
            'protein': ${verbose ? `(${proteinVerboseQuery})[0]` : 'record._to'},
            'ontology term': ${verbose ? `(${ontologyTermVerboseQuery})[0]` : 'edgeRecord._to'},
            'motif_fc': record['motif_fc'], 'motif_pos': record['motif_pos'], 'motif_orient': record['motif_orient'], 'motif_conc': record['motif_conc'], 'motif': record['motif'], 'source': record['source'],
            ${getDBReturnStatements(asbCOSchema).replaceAll('record', 'edgeRecord')},
            'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
          }
        )[0]
    )
    LET GVATdb = (
      FOR record in variantsProteinsEdges
        FILTER record.source == 'GVATdb allele-specific TF binding calls'
        RETURN {
          'sequence_variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
          'protein': ${verbose ? `(${proteinVerboseQuery})[0]` : 'record._to'},
            'log10pvalue': record.log10pvalue, 'p_value': record.p_value, 'hg19_coordinate': record['hg19_coordinate'], 'source': record['source'], 'label': record['label'],
            'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
          }
    )
    LET UKB = (
      FOR record in variantsProteinsEdges
        FILTER record.source == 'UKB'
        RETURN {
          'sequence_variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
          'protein': ${verbose ? `(${proteinVerboseQuery})[0]` : 'record._to'},
            ${getDBReturnStatements(ukbSchema)},
          'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
          }
    )
    LET SEMplComplex = (
        FOR record in variantsProteinsEdges
        FILTER record.source == 'SEMpl' AND record._to LIKE 'complexes/%'
        RETURN {
          'sequence_variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
          'complex': ${verbose ? `(${complexVerboseQuery})[0]` : 'record._to'},
            ${getDBReturnStatements(semplSchema)},
          'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
        }
    )
    LET SEMplProtein = (
        FOR record in variantsProteinsEdges
        FILTER record.source == 'SEMpl' AND record._to LIKE 'proteins/%'
        RETURN {
          'sequence_variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
          'protein': ${verbose ? `(${proteinVerboseQuery})[0]` : 'record._to'},
            ${getDBReturnStatements(semplSchema)},
          'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
        }
    )
    LET array1 = APPEND(ADASTRA, GVATdb)
    LET array2 = APPEND(array1, UKB)
    LET array3 = APPEND(array2, SEMplComplex)
    RETURN APPEND(array3, SEMplProtein)
    `

  const result = (await (await db.query(query)).all()).filter((record) => record !== null)
  return result[0]
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

  const variantsProteinsInput: paramsFormatType = {}
  if (input.source !== undefined) {
    variantsProteinsInput.source = input.source
    delete input.source
  }
  if (input.label !== undefined) {
    variantsProteinsInput.label = input.label
    delete input.label
  }

  let variantsProteinsFilter = getFilterStatements(asbSchema, variantsProteinsInput)
  if (variantsProteinsFilter) {
    variantsProteinsFilter = ` AND ${variantsProteinsFilter}`
  }

  let nameFilters = ''
  if (input.name !== undefined) {
    nameFilters += ` AND record.name == '${input.name as string}'`
  }
  if (input.inverse_name !== undefined) {
    nameFilters += ` AND record.inverse_name == '${input.inverse_name as string}'`
  }

  // eslint-disable-next-line @typescript-eslint/naming-convention
  const variantInput: paramsFormatType = (({ variant_id, spdi, hgvs, rsid, chr, position }) => ({ variant_id, spdi, hgvs, rsid, chr, position }))(input)
  delete input.variant_id
  delete input.spdi
  delete input.hgvs
  delete input.rsid
  delete input.chr
  delete input.position
  const variantIDs = await variantIDSearch(variantInput)

  const query = `
    LET variantsProteinsEdges = (
      FOR record in ${variantsProteinsDatabaseName}
        FILTER record._from IN ['${variantIDs.join('\', \'')}'] ${variantsProteinsFilter} ${nameFilters}
        SORT record._key
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN record
    )
    LET ADASTRA = (
      FOR record in variantsProteinsEdges
        FILTER record.source == 'ADASTRA allele-specific TF binding calls'
        RETURN (
          FOR edgeRecord IN ${variantsProteinsDatabaseName}
          FILTER edgeRecord._from == record._id
          RETURN {
            'sequence_variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
            'protein': ${verbose ? `(${proteinVerboseQuery})[0]` : 'record._to'},
            'ontology term': ${verbose ? `(${ontologyTermVerboseQuery})[0]` : 'edgeRecord._to'},
            'motif_fc': record['motif_fc'], 'motif_pos': record['motif_pos'], 'motif_orient': record['motif_orient'], 'motif_conc': record['motif_conc'], 'motif': record['motif'], 'source': record['source'],
            ${getDBReturnStatements(asbCOSchema).replaceAll('record', 'edgeRecord')},
            'name': record.name,
            'score': (
              FOR vpt IN variants_proteins_terms
              FILTER vpt._from == record._id
              RETURN {
                'biological_context': vpt.biological_context,
                'fdrp_bh_ref': vpt.fdrp_bh_ref,
                'fdrp_bh_alt': vpt.fdrp_bh_alt
              }
            )
          }
        )[0]
    )
    LET GVATdb = (
      FOR record in variantsProteinsEdges
        FILTER record.source == 'GVATdb allele-specific TF binding calls'
        RETURN {
          'sequence_variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
          'protein': ${verbose ? `(${proteinVerboseQuery})[0]` : 'record._to'},
            'log10pvalue': record.log10pvalue, 'p_value': record.p_value, 'hg19_coordinate': record['hg19_coordinate'], 'source': record['source'], 'label': record['label'],
            'name': record.name
          }
    )
    LET UKB =(
      FOR record in variantsProteinsEdges
        FILTER record.source == 'UKB'
        RETURN {
          'sequence_variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
          'protein': ${verbose ? `(${proteinVerboseQuery})[0]` : 'record._to'},
            ${getDBReturnStatements(ukbSchema)},
          'name': record.name
        }
    )

    LET SEMplProtein = (
      FOR record in variantsProteinsEdges
        FILTER record.source == 'IGVF' AND record.label == 'predicted allele specific binding' AND record._to LIKE 'proteins/%'
        RETURN {
          'sequence_variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
          'protein': ${verbose ? `(${proteinVerboseQuery})[0]` : 'record._to'},
            ${getDBReturnStatements(semplSchema)},
          'name': record.name
        }
    )
    LET SEMplComplex = (
      FOR record in variantsProteinsEdges
        FILTER record.source == 'IGVF' AND record.label == 'predicted allele specific binding' AND record._to LIKE 'complexes/%'
        RETURN {
          'sequence_variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
          'complex': ${verbose ? `(${complexVerboseQuery})[0]` : 'record._to'},
            ${getDBReturnStatements(semplSchema)},
          'name': record.name
        }
    )
    LET mergedArray1 = APPEND(ADASTRA, GVATdb)
    LET mergedArray2 = APPEND(mergedArray1, UKB)
    LET mergedArray3 = APPEND(mergedArray2, SEMplProtein)
    RETURN APPEND(mergedArray3, SEMplComplex)
    `

  const result = (await (await db.query(query)).all()).filter((record) => record !== null)
  return result[0]
}

// Only keep cell-type scpecific queries for ASB endpoints here
// /variants/proteins, /proteins/variants -> returns cell-type specific values from hyperedges & generic values from primary edges (motif-relevant values)
const variantsFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/variants', description: descriptions.proteins_variants } })
  .input(proteinsQuery)
  .output(z.array(AsbFormat))
  .query(async ({ input }) => await variantsFromProteinSearch(input))

const proteinsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/proteins', description: descriptions.variants_proteins } })
  .input(variantsQuery)
  .output(z.array(AsbFormat))
  .query(async ({ input }) => await proteinsFromVariantSearch(input))

export const variantsProteinsRouters = {
  proteinsFromVariants,
  variantsFromProteins
}
