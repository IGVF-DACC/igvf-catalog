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

const studyFormat = z.object({
  _id: z.string(),
  // ancestry_initial, ancestry_replication, trait_efos should actually be loaded as arrays not strings
  // if only show in output, then doesn't matter so much
  ancestry_initial: z.string().optional(),
  ancestry_replication: z.string().optional(),
  n_cases: z.string().optional(),
  n_initial: z.string().optional(),
  n_replication: z.string().optional(),
  pmid: z.string().optional(),
  pub_author: z.string().optional(),
  pub_date: z.string().optional(),
  pub_journal: z.string().optional(),
  pub_title: z.string().optional(),
  has_sumstats: z.string().optional(),
  num_assoc_loci: z.string().optional(),
  study_source: z.string().optional(),
  trait_reported: z.string().optional(),
  trait_efos: z.string().optional(),
  trait_category: z.string().optional(),
  source: z.string().optional(),
  version: z.string().optional()
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
