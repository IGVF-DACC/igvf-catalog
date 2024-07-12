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

const MAX_PAGE_SIZE = 1000

const schema = loadSchemaConfig()

const motifsToProteinsFormat = z.object({
  source: z.string().optional(),
  protein: z.string().or(z.array(proteinFormat)).optional(),
  motif: z.string().or(motifFormat).optional()
})

const proteinsQuery = proteinsCommonQueryFormat.merge(commonHumanEdgeParamsFormat).transform(({protein_name, ...rest}) => ({
  name: protein_name,
  ...rest
}))

const motifProteinSchema = schema['motif to protein']
const motifSchema = schema.motif
const proteinSchema = schema.protein

async function proteinsFromMotifSearch (input: paramsFormatType): Promise<any[]> {
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

  const verboseQuery = `
    FOR otherRecord IN ${proteinSchema.db_collection_name}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(proteinSchema).replaceAll('record', 'otherRecord')}}
  `

  const query = `
    LET sources = (
      FOR record in ${motifSchema.db_collection_name}
      ${filterBy}
      RETURN record._id
    )

    FOR record IN ${motifProteinSchema.db_collection_name}
      FILTER record._from IN sources
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        ${getDBReturnStatements(motifProteinSchema)},
        'protein': ${input.verbose === 'true' ? `(${verboseQuery})` : 'record._to'}
      }
  `

  return await (await db.query(query)).all()
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
    FOR otherRecord IN ${motifSchema.db_collection_name}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(motifSchema).replaceAll('record', 'otherRecord')}}
  `

  if (input.protein_id !== undefined) {
    query = `
      FOR record IN ${motifProteinSchema.db_collection_name}
      FILTER record._to == '${proteinSchema.db_collection_name}/${decodeURIComponent(input.protein_id as string)}'
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'motif': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._from'},
        ${getDBReturnStatements(motifProteinSchema)}
      }
    `
  } else {
    let filterBy = ''
    const filterSts = getFilterStatements(proteinSchema, input)
    if (filterSts !== '') {
      filterBy = `FILTER ${filterSts}`
    }

    query = `
      LET targets = (
        FOR record IN ${proteinSchema.db_collection_name}
        ${filterBy}
        RETURN record._id
      )

      FOR record IN ${motifProteinSchema.db_collection_name}
        FILTER record._to IN targets
        SORT record._key
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN {
          'motif': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._from'},
          ${getDBReturnStatements(motifProteinSchema)}
        }
    `
  }

  return await (await db.query(query)).all()
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
