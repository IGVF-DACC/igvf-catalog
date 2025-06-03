import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT, configType } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam, validRegion } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonNodesParamsFormat, geneTypes, geneCollections, geneStudySets } from '../params'
import { metaAPIMiddleware, metaAPIOutput } from '../../../meta'

const MAX_PAGE_SIZE = 500

const schema = loadSchemaConfig()
const humanGeneSchema = schema.gene
const mouseGeneSchema = schema['gene mouse']

export const genesQueryFormat = z.object({
  gene_id: z.string().trim().optional(),
  hgnc: z.string().trim().optional(),
  entrez: z.string().trim().optional(),
  name: z.string().trim().optional(),
  region: z.string().trim().optional(),
  synonym: z.string().trim().optional(),
  collection: geneCollections.optional(),
  study_set: geneStudySets.optional(),
  gene_type: geneTypes.optional()
}).merge(commonNodesParamsFormat)

export const geneFormat = z.object({
  _id: z.string(),
  chr: z.string(),
  start: z.number().nullable(),
  end: z.number().nullable(),
  gene_type: z.string().nullable(),
  name: z.string(),
  strand: z.string().optional().nullable(),
  hgnc: z.string().optional().nullable(),
  entrez: z.string().optional().nullable(),
  collections: z.array(z.string()).optional().nullable(),
  study_sets: z.array(z.string()).optional().nullable(),
  source: z.string(),
  version: z.string(),
  source_url: z.string(),
  synonyms: z.array(z.string()).optional().nullable()
})

export async function nearestGeneSearch (input: paramsFormatType): Promise<any[]> {
  const regionParams = validRegion(input.region as string)

  let geneTypeFilter = ''
  if (input.gene_type !== undefined) {
    geneTypeFilter = `AND record.gene_type == '${input.gene_type as string}'`
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
      FILTER record.chr == '${regionParams[1]}' and record.end < ${regionParams[2]} ${geneTypeFilter}
      SORT record.end DESC
      LIMIT 1
      RETURN {${getDBReturnStatements(schema.gene)}}
    )

    LET RIGHT = (
      FOR record in genes
      FILTER record.chr == '${regionParams[1]}' and record.start > ${regionParams[3]} ${geneTypeFilter}
      SORT record.start
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

export async function findGenesByTextSearch (input: paramsFormatType, geneSchema: configType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const preProcessed = preProcessRegionParam(input)

  const geneName = preProcessed.name as string
  delete preProcessed.name

  const synonym = preProcessed.synonym as string
  delete preProcessed.synonym

  let remainingFilters = getFilterStatements(geneSchema, preProcessed)
  if (remainingFilters) {
    remainingFilters = `FILTER ${remainingFilters}`
  }
  const query = (searchFilters: string[]): string => {
    return `
      FOR record IN ${geneSchema.db_collection_name as string}_text_en_no_stem_inverted_search_alias
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
  if (synonym !== undefined) {
    searchFilters.push(`TOKENS("${decodeURIComponent(synonym)}", "text_en_no_stem") ALL in record.alias`)
  }
  const textObjects = await (await db.query(query(searchFilters))).all()
  if (textObjects.length === 0) {
    searchFilters = []
    if (geneName !== undefined) {
      searchFilters.push(`LEVENSHTEIN_MATCH(record.name, TOKENS("${decodeURIComponent(geneName)}", "text_en_no_stem")[0], 1, false)`)
    }
    if (synonym !== undefined) {
      searchFilters.push(`LEVENSHTEIN_MATCH(record.alias, TOKENS("${decodeURIComponent(synonym)}", "text_en_no_stem")[0], 1, false)`)
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
    input._key = input.gene_id
    delete input.gene_id
  }

  if (input.synonym !== undefined) {
    input.synonyms = input.synonym
    delete input.synonym
  }

  if (input.collection !== undefined) {
    input.collections = input.collection
    delete input.collection
  }

  if (input.study_set !== undefined) {
    input.study_sets = input.study_set
    delete input.study_set
  }

  if (input.entrez !== undefined) {
    if (!(input.entrez.toString().startsWith('ENTREZ'))) {
      input.entrez = `ENTREZ:${input.entrez as string}`
    }
  }

  if (input.hgnc !== undefined) {
    if (!(input.hgnc.toString().startsWith('HGNC'))) {
      input.hgnc = `HGNC:${input.hgnc as string}`
    }
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const preProcessed = preProcessRegionParam(input)
  let filterBy = ''
  const filterSts = getFilterStatements(geneSchema, preProcessed)
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }
  const query = `
    FOR record IN ${geneSchema.db_collection_name as string}
    ${filterBy}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}
    RETURN { ${getDBReturnStatements(geneSchema)} }
  `
  const result = await (await db.query(query)).all()
  if (result.length !== 0) {
    return result
  }
  if (('name' in input && input.name !== undefined) || ('gene_name' in input && input.gene_name !== undefined) || ('synonym' in input && input.synonym !== undefined)) {
    return await findGenesByTextSearch(preProcessed, geneSchema)
  }

  return []
}

const genes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes', description: descriptions.genes } })
  .input(genesQueryFormat)
  .output(metaAPIOutput(z.array(geneFormat)))
  .use(metaAPIMiddleware)
  .query(async ({ input }) => await geneSearch(input))

export const genesRouters = {
  genes
}
