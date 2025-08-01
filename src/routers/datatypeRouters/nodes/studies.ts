import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { descriptions } from '../descriptions'
import { paramsFormatType } from '../_helpers'

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

const schema = loadSchemaConfig()

const schemaObj = schema.study
const router = new RouterFilterBy(schemaObj)

async function studiesSearch (input: paramsFormatType): Promise<any[]> {
  if (input.study_id !== undefined) {
    input._key = `${input.study_id as string}`
    delete input.study_id
  }

  if (input.pmid !== undefined) {
    input.pmid = 'PMID:' + (input.pmid as string)
  }
  return await router.getObjects(input)
}

const studies = publicProcedure
  .meta({ openapi: { method: 'GET', path: `/${router.apiName}`, description: descriptions.studies } })
  .input(studyQueryFormat)
  .output(z.array(studyFormat))
  .query(async ({ input }) => await studiesSearch(input))

export const studiesRouters = {
  studies
}
