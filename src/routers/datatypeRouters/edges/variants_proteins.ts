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

const MAX_PAGE_SIZE = 100

const schema = loadSchemaConfig()

// primary: variants -> proteins (generic context)
const asbSchema = schema['allele specific binding']
const variantSchema = schema['sequence variant']
const proteinSchema = schema['protein']

// secondary: variants -> (edge) proteins, (edge) -> biosample terms (cell-type specific context)
// asb -> ontology term
const asbCOSchema = schema['allele specific binding cell ontology']
const ontologyTermSchema = schema['ontology term']


const AsbQueryFormat = z.object({
  verbose: z.enum(['true', 'false']).default('false'),
  page: z.number().default(0)

})

const AsbFormat = z.object({
  'sequence variant': z.string().or(z.array(variantSimplifiedFormat)).optional(),
  protein: z.string().or(z.array(proteinFormat.omit({ dbxrefs: true }))).optional(),
  'ontology term': z.string().or(z.array(ontologyFormat)).optional(),
  biological_context: z.string().nullable(),
  es_mean_ref: z.string().nullable(),
  es_mean_alt: z.string().nullable(),
  fdrp_bh_ref: z.string().nullable(),
  fdrp_bh_alt: z.string().nullable(),
  motif_fc: z.string().nullable(),
  motif_pos: z.string().nullable(),
  motif_orient: z.string().nullable(),
  motif_conc: z.string().nullable(),
  motif: z.string().nullable(),
  source: z.string().nullable()
})

const variantVerboseQuery = `
    FOR otherRecord IN ${variantSchema.db_collection_name}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
      RETURN {${getDBReturnStatements(variantSchema).replaceAll('record', 'otherRecord')}}
  `
const proteinVerboseQuery = `
  FOR otherRecord IN ${proteinSchema.db_collection_name}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(proteinSchema).replaceAll('record', 'otherRecord')}}
  `

const ontologyTermVerboseQuery = `
  FOR targetRecord IN ${ontologyTermSchema.db_collection_name}
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

  const query = `
    LET proteinIds = (
      FOR record IN ${proteinSchema.db_collection_name}
      FILTER ${getFilterStatements(proteinSchema, input)}
      RETURN record._id
    )

    FOR record in ${asbSchema.db_collection_name}
      FILTER record._to IN proteinIds
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN (
        FOR edgeRecord IN ${asbCOSchema.db_collection_name}
        FILTER edgeRecord._from == record._id
        RETURN {
          'sequence variant': ${verbose ? `(${variantVerboseQuery})` : 'record._from'},
          'protein': ${verbose ? `(${proteinVerboseQuery})` : 'record._to'},
          'ontology term': ${verbose ? `(${ontologyTermVerboseQuery})` : 'edgeRecord._to'},
          ${getDBReturnStatements(asbSchema)},
          ${getDBReturnStatements(asbCOSchema).replaceAll('record', 'edgeRecord') as string}
        }
      )[0]
    `

  return (await (await db.query(query)).all()).filter((record) => record !== null)
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

  const query = `
    LET variantIds = (
      FOR record IN ${variantSchema.db_collection_name}
      FILTER ${getFilterStatements(variantSchema, input)}
      RETURN record._id
    )

    FOR record in ${asbSchema.db_collection_name}
      FILTER record._from IN variantIds
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN (
        FOR edgeRecord IN ${asbCOSchema.db_collection_name}
        FILTER edgeRecord._from == record._id
        RETURN {
          'sequence variant': ${verbose ? `(${variantVerboseQuery})` : 'record._from'},
          'protein': ${verbose ? `(${proteinVerboseQuery})` : 'record._to'},
          'ontology term': ${verbose ? `(${ontologyTermVerboseQuery})` : 'edgeRecord._to'},
          ${getDBReturnStatements(asbSchema)},
          ${getDBReturnStatements(asbCOSchema).replaceAll('record', 'edgeRecord') as string}
        }
      )[0]
    `

    return (await (await db.query(query)).all()).filter((record) => record !== null)
}

const proteinsQuery = proteinsQueryFormat.merge(
  z.object({ limit: z.number().optional() })
).omit({
  organism: true,
  name: true
}).merge(AsbQueryFormat).merge(z.object({protein_name: z.string().optional()})).transform(({protein_name, ...rest}) => ({
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
  .input(variantsQueryFormat.omit({ region: true, funseq_description: true }).merge(AsbQueryFormat).merge(z.object({ limit: z.number().optional() })))
  .output(z.array(AsbFormat))
  .query(async ({ input }) => await proteinsFromVariantSearch(input))

export const variantsProteinsRouters = {
  proteinsFromVariants,
  variantsFromProteins
}
