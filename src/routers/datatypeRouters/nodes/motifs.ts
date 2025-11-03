import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { commonHumanNodesParamsFormat, motifsCommonQueryFormat } from '../params'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 500

const motifSchema = getSchema('data/schemas/nodes/motifs.Motif.json')
const motifCollectionName = (motifSchema.accessible_via as Record<string, any>).name as string

export const motifFormat = z.object({
  name: z.string(),
  tf_name: z.string(),
  length: z.number(),
  pwm: z.array(z.array(z.string().optional())),
  source: z.string(),
  source_url: z.string()
})

async function motifSearch (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  if (input.tf_name !== undefined) {
    input.tf_name = (input.tf_name as string).toUpperCase()
  }

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

  const query = `
    FOR record IN ${motifCollectionName}
    ${filterBy}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(motifSchema)} }
  `
  return await (await db.query(query)).all()
}

const motifs = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/motifs', description: descriptions.motifs } })
  .input(motifsCommonQueryFormat.merge(commonHumanNodesParamsFormat))
  .output(z.array(motifFormat))
  .query(async ({ input }) => await motifSearch(input))

export const motifsRouters = {
  motifs
}
