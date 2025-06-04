import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { QUERY_LIMIT } from '../../../constants'
import { descriptions } from '../descriptions'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { db } from '../../../database'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'

const MAX_PAGE_SIZE = 500

const schema = loadSchemaConfig()
const filesFilesetsSchema = schema['files to file sets']

const LABS = [
  'roderic-guigo',
  'jesse-engreitz',
  'j-michael-cherry',
  'zhiping-weng',
  'nadav-ahituv',
  'bill-majoros'
] as const

const ASSAYS = [
  'HiC', 'RNA-seq', 'ChIA-PET', 'polyA plus RNA-seq', 'ChIP-seq', 'MPRA', 'Mint-ChIP-seq', 'ATAC-seq', 'DNase-seq', 'CAGE'
] as const

const METHOD = [
  'element gene regulatory interaction predictions using EPIraction',
  'element gene regulatory interaction predictions using Distal regulation ENCODE-rE2G',
  'caQTLs',
  'candidate Cis-Regulatory Elements',
  'MPRA',
  'element gene regulatory interactions using DistalRegulationCRISPRdata',
  'functional effect prediction on scope of loci'
] as const

const SOFTWARE = [
  'EPIraction',
  'Distal regulation ENCODE-rE2G',
  'BEDTools',
  'bigWigAverageOverBed',
  'MPRAflow tsv-to-bed',
  'DistalRegulationCRISPRdata',
  'BlueSTARR'
] as const

const filesFilesetsQueryFormat = z.object({
  file_fileset_id: z.string().optional(),
  fileset_id: z.string().optional(),
  lab: z.enum(LABS).optional(),
  preferred_assay_title: z.enum(ASSAYS).optional(),
  method: z.enum(METHOD).optional(),
  donor_id: z.string().optional(),
  sample_term: z.string().optional(),
  sample_summary: z.string().optional(),
  software: z.enum(SOFTWARE).optional(),
  page: z.number().default(0),
  limit: z.number().optional()
// eslint-disable-next-line @typescript-eslint/naming-convention
}).transform(({ preferred_assay_title, fileset_id, file_fileset_id, donor_id, sample_term, sample_summary, ...rest }) => ({
  id: file_fileset_id,
  file_set_id: fileset_id,
  preferred_assay_titles: preferred_assay_title,
  donors: donor_id,
  samples: sample_term,
  simple_sample_summaries: sample_summary,
  ...rest
}))

const filesFilesetsFormat = z.object({
  _id: z.string(),
  file_set_id: z.string(),
  lab: z.string(),
  preferred_assay_titles: z.array(z.string()).nullish(),
  assay_term_ids: z.array(z.string()).nullish(),
  method: z.string(),
  class: z.string(),
  software: z.array(z.string()).nullish(),
  samples: z.array(z.string()).nullish(),
  sample_ids: z.array(z.string()).nullish(),
  simple_sample_summaries: z.array(z.string()).nullish(),
  donors: z.array(z.string()).nullish(),
  source: z.string()
})

async function filesFilesetsSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  if (input.samples !== undefined) {
    input.samples = `ontology_terms/${input.samples as string}`
  }

  if (input.donors !== undefined) {
    input.donors = `donors/${input.donors as string}`
  }

  let filterBy = ''
  const filterSts = getFilterStatements(filesFilesetsSchema, input)
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }

  const query = `
    FOR record IN ${filesFilesetsSchema.db_collection_name as string}
    ${filterBy}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(filesFilesetsSchema)} }
  `

  return await (await db.query(query)).all()
}

const filesFilesets = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/files-filesets', description: descriptions.files_fileset } })
  .input(filesFilesetsQueryFormat)
  .output(z.array(filesFilesetsFormat))
  .query(async ({ input }) => await filesFilesetsSearch(input))

export const filesFilesetsRouters = {
  filesFilesets
}
