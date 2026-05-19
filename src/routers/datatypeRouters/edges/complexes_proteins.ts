import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { proteinByIDQuery, proteinFormat } from '../nodes/proteins'
import { complexSearch, complexFormat } from '../nodes/complexes'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { commonComplexQueryFormat, commonHumanEdgeParamsFormat, proteinsCommonQueryFormat } from '../params'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 50

const linkedFeatureFormat = z.object({
  participantId: z.string(),
  ranges: z.array(z.string())
})

/** Edge fields from complexes_proteins.EBIComplex accessible_via.return; only present on EBI source edges. */
const proteinComplexFormat = z.object({
  protein: z.string().or(proteinFormat).optional(),
  complex: z.string().or(complexFormat).optional(),
  name: z.string(),
  stoichiometry: z.number().nullish(),
  chain_id: z.string().nullish(),
  isoform_id: z.string().nullish(),
  number_of_paralogs: z.number().nullish(),
  linked_features: z.array(linkedFeatureFormat).nullish(),
  source: z.string().optional(),
  source_url: z.string().optional()
})

const complextToProteinSchema = getSchema('data/schemas/edges/complexes_proteins.EBIComplex.json')
const complextToProteinCollectionName = complextToProteinSchema.db_collection_name as string
const complexSchema = getSchema('data/schemas/nodes/complexes.EBIComplex.json')
const complexCollectionName = complexSchema.db_collection_name as string
const proteinSchema = getSchema('data/schemas/nodes/proteins.GencodeProtein.json')
const proteinCollectionName = proteinSchema.db_collection_name as string

const proteinVerboseQuery = `
  FOR otherRecord IN ${proteinCollectionName}
  FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
  RETURN {${getDBReturnStatements(proteinSchema).replaceAll('record', 'otherRecord')}}
`

const complexVerboseQuery = `
  FOR otherRecord IN ${complexCollectionName}
  FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
  RETURN {${getDBReturnStatements(complexSchema).replaceAll('record', 'otherRecord')}}
`

async function complexesFromProteinSearch (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const verbose = input.verbose === 'true'

  let targets
  if (input.protein_id !== undefined) {
    targets = `LET targets = ${proteinByIDQuery(input.protein_id as string)}`
  } else {
    input.name = input.protein_name
    input.uniprot_names = input.uniprot_name
    input.uniprot_full_names = input.uniprot_full_name
    delete input.uniprot_name
    delete input.uniprot_full_name
    delete input.protein_name

    targets = `
      LET targets = (
        FOR record IN ${proteinCollectionName}
        FILTER ${getFilterStatements(proteinSchema, input)}
        RETURN record._id
      )`
  }

  const query = `
    ${targets}
    FOR record IN ${complextToProteinCollectionName}
      FILTER record._to IN targets
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'protein': ${verbose ? `(${proteinVerboseQuery})[0]` : 'record._to'},
        'complex': ${verbose ? `(${complexVerboseQuery})[0]` : 'record._from'},
        ${getDBReturnStatements(complextToProteinSchema)},
        'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
      }
  `
  return await (await db.query(query)).all()
}

async function proteinsFromComplexesSearch (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const verbose = input.verbose === 'true'

  let complexIDs
  if (input.complex_id !== undefined) {
    complexIDs = [`${complexCollectionName}/${decodeURIComponent(input.complex_id as string)}`]
  } else {
    const complexes = await complexSearch(input)
    complexIDs = complexes.map((c) => `complexes/${c._id as string}`)
  }

  const query = `
    FOR record IN ${complextToProteinCollectionName}
      FILTER record._from IN ['${complexIDs.join('\',\'')}']
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'complex': ${verbose ? `(${complexVerboseQuery})[0]` : 'record._from'},
        'protein': ${verbose ? `(${proteinVerboseQuery})[0]` : 'record._to'},
        ${getDBReturnStatements(complextToProteinSchema)},
        'name': record.name
      }
  `

  return await (await db.query(query)).all()
}

const proteinsQuery = proteinsCommonQueryFormat.merge(commonHumanEdgeParamsFormat)

// eslint-disable-next-line @typescript-eslint/naming-convention
const complexQuery = commonComplexQueryFormat.merge(commonHumanEdgeParamsFormat).transform(({ complex_name, ...rest }) => ({
  name: complex_name,
  ...rest
}))

const proteinsFromComplexes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/complexes/proteins', description: descriptions.complexes_proteins } })
  .input(complexQuery)
  .output(z.array(proteinComplexFormat))
  .query(async ({ input }) => await proteinsFromComplexesSearch(input))

const complexesFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/complexes', description: descriptions.proteins_complexes } })
  .input(proteinsQuery)
  .output(z.array(proteinComplexFormat))
  .query(async ({ input }) => await complexesFromProteinSearch(input))

export const complexesProteinsRouters = {
  proteinsFromComplexes,
  complexesFromProteins
}
