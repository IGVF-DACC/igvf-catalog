import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { descriptions } from '../descriptions'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { getSchema } from '../schema'

const schemaObj = getSchema('data/schemas/nodes/studies.GWAS.json')
const studyCollectionName = (schemaObj.accessible_via as Record<string, any>).name as string

const studyQueryFormat = z.object({
  study_id: z.string().trim().optional(),
  pmid: z.string().trim().optional(),
  page: z.number().default(0)
})

export const studyFormat = z.object({
  _id: z.string(),
  name: z.string(),
  // ancestry_initial, ancestry_replication, trait_efos should actually be loaded as arrays not strings
  // if only show in output, then doesn't matter so much
  ancestry_initial: z.string().nullable(),
  ancestry_replication: z.string().nullable(),
  n_cases: z.string().nullable(),
  n_initial: z.string().nullable(),
  n_replication: z.string().nullable(),
  pmid: z.string().nullable(),
  pub_author: z.string().nullable(),
  pub_date: z.string().nullable(),
  pub_journal: z.string().nullable(),
  pub_title: z.string().nullable(),
  has_sumstats: z.string().nullable(),
  num_assoc_loci: z.string().nullable(),
  study_source: z.string().nullable(),
  trait_reported: z.string().nullable(),
  trait_efos: z.string().nullable(),
  trait_category: z.string().nullable(),
  source: z.string().optional(),
  study_type: z.string().nullable(),
  version: z.string().nullable()
})

async function studiesSearch (input: paramsFormatType): Promise<any[]> {
  if (input.study_id !== undefined) {
    input._key = `${input.study_id as string}`
    delete input.study_id
  }

  if (input.pmid !== undefined) {
    input.pmid = 'PMID:' + (input.pmid as string)
  }

  const query = `
    FOR record IN ${studyCollectionName}
    FILTER ${getFilterStatements(schemaObj, input)}
    SORT record._key
    LIMIT ${input.page as number * QUERY_LIMIT}, ${QUERY_LIMIT}
    RETURN { ${getDBReturnStatements(schemaObj)} }
  `
  return await (await db.query(query)).all()
}

const studies = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/studies', description: descriptions.studies } })
  .input(studyQueryFormat)
  .output(z.array(studyFormat))
  .query(async ({ input }) => await studiesSearch(input))

export const studiesRouters = {
  studies
}
