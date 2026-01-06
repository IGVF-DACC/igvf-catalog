import { z } from 'zod'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { paramsFormatType, preProcessRegionParam, getDBReturnStatements, getFilterStatements } from '../_helpers'
import { descriptions } from '../descriptions'
import { QUERY_LIMIT } from '../../../constants'
import { genomicElementSourceAnnotation, commonNodesParamsFormat, genomicElementSource, genomicElementType } from '../params'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 1000

const METHODS = [
  'ENCODE-rE2G',
  'lentiMPRA',
  'candidate Cis-Regulatory Elements',
  'MPRA',
  'caQTL',
  'CRISPR FACS screen',
  'Perturb-seq',
  'CRISPR enhancer perturbation screens'
] as const

export const genomicElementsQueryFormat = z.object({
  region: z.string().trim().optional(),
  source_annotation: genomicElementSourceAnnotation.optional(),
  type: genomicElementType.optional(),
  method: z.enum(METHODS).optional(),
  source: genomicElementSource.optional()
}).merge(commonNodesParamsFormat)

export const genomicElementFormat = z.object({
  chr: z.string(),
  start: z.number(),
  end: z.number(),
  name: z.string(),
  method: z.string().nullish(),
  source_annotation: z.string().nullable(),
  type: z.string(),
  source: z.string(),
  source_url: z.string()
})

const humanSchemaObj = getSchema('data/schemas/nodes/genomic_elements.CCRE.json')
const mouseSchemaObj = getSchema('data/schemas/nodes/mm_genomic_elements.HumanMouseElementAdapter.json')

async function genomicElementSearch (input: paramsFormatType): Promise<any[]> {
  let schema = humanSchemaObj
  if (input.organism === 'Mus musculus') {
    schema = mouseSchemaObj
  }
  const schemaCollectionName = schema.db_collection_name as string
  delete input.organism

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = ` AND record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
    delete input.files_fileset
  }

  let filterBy = ''
  const filterSts = getFilterStatements(schema, preProcessRegionParam(input))
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts} ${filesetFilter}`
  } else {
    if (filesetFilter !== '') {
      filterBy = `FILTER ${filesetFilter.replace(' AND ', '')}`
    } else {
      throw new Error('At least one filter must be provided.')
    }
  }

  const query = `
    FOR record IN ${schemaCollectionName}
    ${filterBy}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(schema)} }
  `
  return await (await db.query(query)).all()
}

const genomicElements = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genomic-elements', description: descriptions.genomic_elements } })
  .input(genomicElementsQueryFormat.merge(z.object({ files_fileset: z.string().optional(), limit: z.number().optional() })))
  .output(z.array(genomicElementFormat))
  .query(async ({ input }) => await genomicElementSearch(input))

export const genomicRegionsRouters = {
  genomicElements
}
