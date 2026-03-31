import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { geneSearch } from '../nodes/genes'
import { paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonNodesParamsFormat, genesCommonQueryFormat } from '../params'
import { getSchema, getCollectionEnumValuesOrThrow } from '../schema'

const MAX_PAGE_SIZE = 500
const METHODS = getCollectionEnumValuesOrThrow('edges', 'genomic_elements_genes', 'method')

const geneSchema = getSchema('data/schemas/nodes/genes.GencodeGene.json')
const geneCollectionName = geneSchema.db_collection_name as string

const genesGenomicElementsInputFormat = genesCommonQueryFormat.merge(z.object({
  gene_id: z.string().optional(),
  method: z.enum(METHODS).optional(),
  files_fileset: z.string().optional()
}).merge(commonNodesParamsFormat).omit({ organism: true }))

const elementOutputFormat = z.object({
  id: z.string(),
  cell_type: z.string().nullish(),
  score: z.number().nullish(),
  model: z.string().nullish(),
  dataset: z.string().nullish(),
  element_type: z.string().nullish(),
  element_chr: z.string().nullish(),
  element_start: z.number().nullish(),
  element_end: z.number().nullish(),
  name: z.string(),
  method: z.string().optional(),
  class: z.string().optional(),
  files_filesets: z.string().nullish()
})

const geneOutputFormat = z.object({
  name: z.string(),
  _id: z.string(),
  start: z.number(),
  end: z.number(),
  chr: z.string()
})

const genesGenomicElementsOutputFormat = z.array(z.object({
  gene: geneOutputFormat,
  elements: z.array(elementOutputFormat).or(elementOutputFormat)
}))

async function findGenomicElementsFromGene (input: paramsFormatType): Promise<any> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = ` AND record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
  }

  let methodFilter = ''
  if (input.method !== undefined) {
    methodFilter = ` AND record.method == '${input.method as string}'`
    delete input.method
  }

  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { gene_id, hgnc_id, gene_name: name, alias, organism } = input
  const geneInput: paramsFormatType = { gene_id, hgnc_id, name, alias, organism, page: 0 }
  delete input.gene_id
  delete input.hgnc_id
  delete input.alias
  delete input.gene_name
  delete input.organism
  const empty = Object.entries(geneInput).filter(([k]) => k !== 'page').every(([, v]) => v === undefined)

  let geneIDs: string[] = []
  if (!empty) {
    const genes = await geneSearch(geneInput)
    geneIDs = genes.map(gene => `${geneCollectionName}/${gene._id as string}`)

    if (geneIDs.length === 0) {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: 'Gene not found.'
      })
    }
  } else {
    if (filesetFilter !== '') {
      filesetFilter = filesetFilter.replace('AND', '')
    }

    if (methodFilter !== '' && filesetFilter === '') {
      methodFilter = methodFilter.replace('AND', '')
    }

    if (filesetFilter === '' && methodFilter === '') {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: 'At least one parameter must be defined.'
      })
    }
  }

  const query = `
    FOR record IN genomic_elements_genes
    FILTER ${empty ? '' : `record._to IN ['${geneIDs.join('\', \'')}']`} ${filesetFilter} ${methodFilter}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}

    LET genomicElement = DOCUMENT(record._from)

    COLLECT gene = DOCUMENT(record._to) INTO rows = {
      id: record._from,
      cell_type: record.biological_context,
      score: record.score,
      model: record.source,
      files_filesets: record.files_filesets,
      dataset: record.source_url,
      element_type: genomicElement.type,
      element_chr: genomicElement.chr,
      element_start: genomicElement.start,
      element_end: genomicElement.end,
      name: record.inverse_name,
      class: record.class,
      method: record.method
    }

    RETURN {
      gene,
      elements: rows
    }
  `

  return (await (await db.query(query)).all())
}

const enhancerGenePredictions = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/enhancer-gene-predictions', description: descriptions.enhancer_gene_predictions } })
  .input(genesGenomicElementsInputFormat)
  .output(genesGenomicElementsOutputFormat)
  .query(async ({ input }) => await findGenomicElementsFromGene(input))

export const enhancerGenePredictionsRouters = {
  enhancerGenePredictions
}
