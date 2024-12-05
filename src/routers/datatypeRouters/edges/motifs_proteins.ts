import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { proteinFormat } from '../nodes/proteins'
import { motifFormat } from '../nodes/motifs'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { commonHumanEdgeParamsFormat, motifsCommonQueryFormat, proteinsCommonQueryFormat } from '../params'
import { complexFormat } from '../nodes/complexes'

const MAX_PAGE_SIZE = 1000

const schema = loadSchemaConfig()

const motifsToProteinsFormat = z.object({
  source: z.string().optional(),
  protein: z.string().or(proteinFormat).optional(),
  complex: z.string().or(complexFormat).optional(),
  motif: z.string().or(motifFormat).optional()
})

// eslint-disable-next-line @typescript-eslint/naming-convention
const proteinsQuery = proteinsCommonQueryFormat.merge(commonHumanEdgeParamsFormat).transform(({ protein_name, ...rest }) => ({
  name: protein_name,
  ...rest
}))

const motifProteinSchema = schema['motif to protein']
const motifSchema = schema.motif
const proteinSchema = schema.protein
const complexSchema = schema.complex
const complexesProteinsSchema = schema['complex to protein']

async function proteinsFromMotifSearch (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  if (input.name !== undefined) {
    input.tf_name = (input.name as string).toUpperCase()
  }
  delete input.name

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filterBy = ''
  const filterSts = getFilterStatements(motifSchema, input)
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }

  const verboseQueryProtein = `
    FOR otherRecord IN ${proteinSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(proteinSchema).replaceAll('record', 'otherRecord')}}
  `
  const verboseQueryComplex = `
    FOR otherRecord IN ${complexSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(complexSchema).replaceAll('record', 'otherRecord')}}
  `

  const query = `
    LET sources = (
      FOR record in ${motifSchema.db_collection_name as string}
      ${filterBy}
      RETURN record._id
    )
    LET motifsProteins = (

    FOR record IN ${motifProteinSchema.db_collection_name as string}
      FILTER record._from IN sources and record._to LIKE 'proteins/%'
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        motif: record._key,
        'source': record['source'],
        'protein': ${input.verbose === 'true' ? `(${verboseQueryProtein})[0]` : 'record._to'}
      }
   )
    LET motifsComplexes = (
      FOR record IN ${motifProteinSchema.db_collection_name as string}
        FILTER record._from IN sources and record._to LIKE 'complexes/%'
        SORT record._key
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN {
          motif: record._key,
          'source': record['source'],
          'complex': ${input.verbose === 'true' ? `(${verboseQueryComplex})[0]` : 'record._to'}
        }
    )
    RETURN APPEND(motifsProteins, motifsComplexes)
  `
  const result = (await (await db.query(query)).all()).filter((record) => record !== null)
  return result[0]
}

async function motifsFromProteinSearch (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  let query

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const verboseQuery = `
    FOR otherRecord IN ${motifSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(motifSchema).replaceAll('record', 'otherRecord')}}
  `

  if (input.protein_id !== undefined) {
    query = `
      LET proteinsMotifs = (
      FOR record IN ${motifProteinSchema.db_collection_name as string}
      FILTER record._to == '${proteinSchema.db_collection_name as string}/${decodeURIComponent(input.protein_id as string)}'
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'motif': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._from'},
        'protein': record._to,
        'source': record.source
      }
      )
      LET complexes = (
        FOR record IN ${complexesProteinsSchema.db_collection_name as string}
        FILTER record._to == '${proteinSchema.db_collection_name as string}/${decodeURIComponent(input.protein_id as string)}'
        SORT record._key
        LIMIT 0, ${limit}
        RETURN record._from
      )
      LET complexesMotifs = (
        FOR record IN ${motifProteinSchema.db_collection_name as string}
        FILTER record._to IN complexes
        SORT record._key
        LIMIT 0, ${limit}
        RETURN {
          'motif': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._from'},
          'complex': record._to,
          'source': record.source
        }
      )
      RETURN APPEND(proteinsMotifs, complexesMotifs)
    `
  } else {
    let filterBy = ''
    const filterSts = getFilterStatements(proteinSchema, input)
    if (filterSts !== '') {
      filterBy = `FILTER ${filterSts}`
    }

    query = `
      LET proteins = (
        FOR record IN ${proteinSchema.db_collection_name as string}
        ${filterBy}
        RETURN record._id
      )
      LET complexes = (
        FOR record IN ${complexesProteinsSchema.db_collection_name as string}
        FILTER record._to IN proteins
        SORT record._key
        RETURN record._from

      )
      LET motifsProteins = (

      FOR record IN ${motifProteinSchema.db_collection_name as string}
        FILTER record._to IN proteins
        SORT record._key
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN {
          'motif': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._from'},
          'protein': record._to,
          'source': record.source
        }
      )
      LET motifsComplexes = (
        FOR record IN ${motifProteinSchema.db_collection_name as string}
          FILTER record._to IN complexes
          SORT record._key
          LIMIT ${input.page as number * limit}, ${limit}
          RETURN {
            'motif': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._from'},
            'complex': record._to,
            'source': record.source
            }
      )
      RETURN APPEND(motifsProteins, motifsComplexes)

    `
  }
  const result = (await (await db.query(query)).all()).filter((record) => record !== null)
  return result[0]
}

const motifsFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/motifs', description: descriptions.proteins_motifs } })
  .input(proteinsQuery)
  .output(z.array(motifsToProteinsFormat))
  .query(async ({ input }) => await motifsFromProteinSearch(input))

// motifs shouldn't need query by ID endpoints
const proteinsFromMotifs = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/motifs/proteins', description: descriptions.motifs_proteins } })
  .input(motifsCommonQueryFormat.merge(commonHumanEdgeParamsFormat))
  .output(z.array(motifsToProteinsFormat))
  .query(async ({ input }) => await proteinsFromMotifSearch(input))

export const motifsProteinsRouters = {
  proteinsFromMotifs,
  motifsFromProteins
}
