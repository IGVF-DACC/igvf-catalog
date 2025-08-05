import { z } from 'zod'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { paramsFormatType, preProcessRegionParam, getDBReturnStatements, getFilterStatements } from '../_helpers'
import { descriptions } from '../descriptions'
import { QUERY_LIMIT } from '../../../constants'
import { sourceAnnotation, commonNodesParamsFormat, genomicElementSource, genomicElementType } from '../params'

const MAX_PAGE_SIZE = 1000

const schema = loadSchemaConfig()

export const genomicElementsQueryFormat = z.object({
  region: z.string().trim().optional(),
  source_annotation: sourceAnnotation.optional(),
  type: genomicElementType.optional(),
  source: genomicElementSource.optional()
}).merge(commonNodesParamsFormat)

export const genomicElementFormat = z.object({
  chr: z.string(),
  start: z.number(),
  end: z.number(),
  name: z.string(),
  source_annotation: z.string().nullable(),
  type: z.string(),
  source: z.string(),
  source_url: z.string()
})

const humanSchemaObj = schema['genomic element']
const mouseSchemaObj = schema['genomic element mouse']

async function genomicElementSearch (input: paramsFormatType): Promise<any[]> {
  let schema = humanSchemaObj
  if (input.organism === 'Mus musculus') {
    schema = mouseSchemaObj
  }
  delete input.organism

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filterBy = ''
  const filterSts = getFilterStatements(schema, preProcessRegionParam(input))
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }

  const query = `
    FOR record IN ${schema.db_collection_name as string}
    ${filterBy}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(schema)} }
  `
  return await (await db.query(query)).all()
}

const genomicElements = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genomic-elements', description: descriptions.genomic_elements } })
  .input(genomicElementsQueryFormat.merge(z.object({ limit: z.number().optional() })))
  .output(z.array(genomicElementFormat))
  .query(async ({ input }) => await genomicElementSearch(input))

export const genomicRegionsRouters = {
  genomicElements
}
