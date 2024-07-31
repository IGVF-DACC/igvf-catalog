import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT, configType } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam, validRegion } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonNodesParamsFormat, geneTypes } from '../params'

const MAX_PAGE_SIZE = 500

const schema = loadSchemaConfig()
const humanGeneSchema = schema.gene
const mouseGeneSchema = schema['gene mouse']

export const genesQueryFormat = z.object({
  gene_id: z.string().trim().optional(),
  hgnc: z.string().trim().optional(),
  name: z.string().trim().optional(),
  region: z.string().trim().optional(),
  alias: z.string().trim().optional(),
  gene_type: geneTypes.optional()
}).merge(commonNodesParamsFormat)

export const geneFormat = z.object({
  _id: z.string(),
  chr: z.string(),
  start: z.number().nullable(),
  end: z.number().nullable(),
  gene_type: z.string().nullable(),
  name: z.string(),
  hgnc: z.string().optional().nullable(),
  source: z.string(),
  version: z.string(),
  source_url: z.string(),
  alias: z.array(z.string()).optional().nullable()
})

export async function nearestGeneSearch (input: paramsFormatType): Promise<any[]> {
  const regionParams = validRegion(input.region as string)

  let geneTypeFilter = ''
  if (input.gene_type !== undefined) {
    geneTypeFilter = `AND record.gene_type == '${input.gene_type}'`
  }

  if (regionParams === null) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Region format invalid. Please use the format as the example: "chr1:12345-54321"'
    })
  }

  const inRegionQuery = `
    FOR record in genes
    FILTER ${getFilterStatements(schema['sequence variant'], preProcessRegionParam(input))}
    RETURN {${getDBReturnStatements(schema.gene)}}
  `

  const codingRegionGenes = await (await db.query(inRegionQuery)).all()

  if (codingRegionGenes.length !== 0) {
    return codingRegionGenes
  }

  const nearestQuery = `
    LET LEFT = (
      FOR record in genes
      FILTER record.chr == '${regionParams[1]}' and record['end:long'] < ${regionParams[2]} ${geneTypeFilter}
      SORT record['end:long'] DESC
      LIMIT 1
      RETURN {${getDBReturnStatements(schema.gene)}}
    )

    LET RIGHT = (
      FOR record in genes
      FILTER record.chr == '${regionParams[1]}' and record['start:long'] > ${regionParams[3]} ${geneTypeFilter}
      SORT record['start:long']
      LIMIT 1
      RETURN {${getDBReturnStatements(schema.gene)}}
    )

    RETURN UNION(LEFT, RIGHT)
  `

  const nearestGenes = await (await db.query(nearestQuery)).all()
  if (nearestGenes !== undefined) {
    return nearestGenes[0]
  }

  return []
}

async function findGeneByID (geneId: string, geneSchema: configType): Promise<any[]> {
  const query = `
    FOR record IN ${geneSchema.db_collection_name as string}
    FILTER record._key == '${decodeURIComponent(geneId)}'
    RETURN { ${getDBReturnStatements(geneSchema)} }
  `
  const record = (await (await db.query(query)).all())

  if (record === undefined) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: `Record ${geneId} not found.`
    })
  }

  return record
}

async function findGenes (input: paramsFormatType, geneSchema: configType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filterBy = ''
  const filterSts = getFilterStatements(geneSchema, input)
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }

  const query = `
    FOR record IN ${geneSchema.db_collection_name as string}
    ${filterBy}
    SORT record.chr
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(geneSchema)} }
  `
  return await (await db.query(query)).all()
}

async function findGenesByTextSearch (input: paramsFormatType, geneSchema: configType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const preProcessed = preProcessRegionParam(input)

  const geneName = preProcessed.name as string
  delete preProcessed.name

  const alias = preProcessed.alias as string
  delete preProcessed.alias

  let remainingFilters = getFilterStatements(geneSchema, preProcessed)
  if (remainingFilters) {
    remainingFilters = `FILTER ${remainingFilters}`
  }
  const query = (searchFilters: string[]): string => {
    return `
      FOR record IN ${geneSchema.db_collection_name as string}_fuzzy_search_alias
        SEARCH ${searchFilters.join(' AND ')}
        ${remainingFilters}
        LIMIT ${input.page as number * limit}, ${limit}
        SORT BM25(record) DESC
        RETURN { ${getDBReturnStatements(geneSchema)} }
    `
  }

  let searchFilters = []
  if (geneName !== undefined) {
    searchFilters.push(`TOKENS("${decodeURIComponent(geneName)}", "text_en_no_stem") ALL in record.name`)
  }
  if (alias !== undefined) {
    searchFilters.push(`TOKENS("${decodeURIComponent(alias)}", "text_en_no_stem") ALL in record.alias`)
  }
  const textObjects = await (await db.query(query(searchFilters))).all()
  if (textObjects.length === 0) {
    searchFilters = []
    if (geneName !== undefined) {
      searchFilters.push(`LEVENSHTEIN_MATCH(record.name, TOKENS("${decodeURIComponent(geneName)}", "text_en_no_stem")[0], 1, false)`)
    }
    if (alias !== undefined) {
      searchFilters.push(`LEVENSHTEIN_MATCH(record.alias, TOKENS("${decodeURIComponent(alias)}", "text_en_no_stem")[0], 1, false)`)
    }

    return await (await db.query(query(searchFilters))).all()
  }
  return textObjects
}

export async function geneSearch (input: paramsFormatType): Promise<any[]> {
  let geneSchema = humanGeneSchema

  if (input.organism === 'Mus musculus') {
    geneSchema = mouseGeneSchema
  }

  delete input.organism
  if (input.gene_id !== undefined) {
    return await findGeneByID(input.gene_id as string, geneSchema)
  }

  const preProcessed = preProcessRegionParam(input)
  if (('gene_name' in input && input.gene_name != undefined) || ('alias' in input && input.alias !== undefined)) {
    return findGenesByTextSearch(preProcessed, geneSchema)
  }

  return await findGenes(preProcessed, geneSchema)
}

const genes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes', description: descriptions.genes } })
  .input(genesQueryFormat)
  .output(z.array(geneFormat))
  .query(async ({ input }) => await geneSearch(input))

export const genesRouters = {
  genes
}
