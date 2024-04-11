import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { proteinFormat, proteinsQueryFormat } from '../nodes/proteins'
import { complexSearch, complexFormat, complexQueryFormat } from '../nodes/complexes'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'

const MAX_PAGE_SIZE = 50

const proteinComplexFormat = z.object({
  source: z.string().optional(),
  source_url: z.string().optional(),
  protein: z.string().or(z.array(proteinFormat)).optional(),
  complex: z.string().or(complexFormat).optional()
})

const schema = loadSchemaConfig()
const complextToProteinSchema = schema['complex to protein']
const complexSchema = schema.complex
const proteinSchema = schema.protein

async function complexesFromProteinSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const verboseQuery = `
      FOR otherRecord IN ${complexSchema.db_collection_name}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
      RETURN {${getDBReturnStatements(complexSchema).replaceAll('record', 'otherRecord')}}
    `

  let targets
  if (input.protein_id !== undefined) {
    targets = `LET targets = ['${proteinSchema.db_collection_name}/${decodeURIComponent(input.protein_id as string)}']`
  } else {
    targets = `
      LET targets = (
        FOR record IN ${proteinSchema.db_collection_name}
        FILTER ${getFilterStatements(proteinSchema, input)}
        RETURN record._id
      )`
  }

  const query = `
    ${targets}
    FOR record IN ${complextToProteinSchema.db_collection_name}
      FILTER record._to IN targets
      SORT record.chr
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'complex': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._from'},
        ${getDBReturnStatements(complextToProteinSchema)}
      }
  `

  console.log(query)
  return await (await db.query(query)).all()
}

async function proteinsFromComplexesSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const proteinVerboseQuery = `
    FOR otherRecord IN ${proteinSchema.db_collection_name}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
      RETURN {${getDBReturnStatements(proteinSchema).replaceAll('record', 'otherRecord')}}
  `

  let complexIDs
  if (input.complex_id !== undefined) {
    complexIDs = [`${complexSchema.db_collection_name}/${decodeURIComponent(input.complex_id as string)}`]
  } else {
    const complexes = await complexSearch(input)
    complexIDs = complexes.map((c) => `complexes/${c._id as string}`)
  }

  const query = `
    FOR record IN ${complextToProteinSchema.db_collection_name}
      FILTER record._from IN ['${complexIDs.join('\',\'')}']
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'protein': ${input.verbose == 'true' ? `(${proteinVerboseQuery})` : 'record._to'},
        ${getDBReturnStatements(complextToProteinSchema)},
      }
  `

  return await (await db.query(query)).all()
}

const proteinsQuery = proteinsQueryFormat.omit({
  organism: true,
  name: true
}).merge(z.object({
  protein_name: z.string().optional(),
  verbose: z.enum(['true', 'false']).default('false'),
  limit: z.number().optional()
})).transform(({protein_name, ...rest}) => ({
  name: protein_name,
  ...rest
}))

const proteinsFromComplexes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/complexes/proteins', description: descriptions.complexes_proteins } })
  .input(complexQueryFormat.merge(z.object({ verbose: z.enum(['true', 'false']).default('false'), limit: z.number().optional() })))
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
