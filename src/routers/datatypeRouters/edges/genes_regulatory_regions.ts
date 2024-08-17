import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { geneSearch, singleGeneQueryFormat } from '../nodes/genes'
import { commonNodesParamsFormat } from '../params'

const MAX_PAGE_SIZE = 500

const schema = loadSchemaConfig()

const predictionFromGeneFormat = z.object({
  gene: z.object({
    name: z.string(),
    id: z.string(),
    start: z.number(),
    end: z.number(),
    chr: z.string()
  }),
  predictions: z.array(z.object({
    id: z.string(),
    cell_type: z.string(),
    score: z.number(),
    model: z.string(),
    dataset: z.string(),
    enhancer_type: z.string(),
    enhancer_start: z.number(),
    enhancer_end: z.number()
  }))
})

const regulatoryRegionToGeneSchema = schema['regulatory element to gene expression association']

async function findPredictionsFromGene (input: paramsFormatType): Promise<any> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const page = input.page as number

  input.page = 0
  input.organism = 'Homo sapiens'
  const genes = (await geneSearch(input))

  if (genes.length === 0) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Gene not found.'
    })
  }

  // assuming unique return
  // input params are IDs only
  const gene = genes[0]

  const query = `
    FOR record IN ${regulatoryRegionToGeneSchema.db_collection_name as string}
    FILTER record._to == 'genes/${gene._id as string}'
    SORT record._key
    LIMIT ${page * limit}, ${limit}
    LET regulatoryRegion = (
      FOR otherRecord IN regulatory_regions
      FILTER otherRecord._id == record._from
      RETURN { type: otherRecord.type, start: otherRecord['start:long'], end: otherRecord['end:long'] }
    )[0]
    RETURN {
      'id': record._from,
      'cell_type': DOCUMENT(record.biological_context)['name'],
      'score': record['score:long'],
      'model': record.source,
      'dataset': record.source_url,
      'enhancer_type': regulatoryRegion.type,
      'enhancer_start': regulatoryRegion.start,
      'enhancer_end': regulatoryRegion.end
    }
  `

  const regulatoryRegionGenes = await (await db.query(query)).all()
  const stuff = {
    gene: {
      name: gene.name,
      id: gene._id,
      start: gene.start,
      end: gene.end,
      chr: gene.chr
    },
    predictions: regulatoryRegionGenes
  }
  console.log(stuff)
  return stuff
}

const regulatoryRegionsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/predictions', description: descriptions.genes_predictions } })
  .input(singleGeneQueryFormat.merge(commonNodesParamsFormat).omit({ organism: true }))
  .output(predictionFromGeneFormat)
  .query(async ({ input }) => await findPredictionsFromGene(input))

export const genesRegulatoryRegionsRouters = {
  regulatoryRegionsFromGenes
}
