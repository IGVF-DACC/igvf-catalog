import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { commonNodesParamsFormat } from '../params'
import { TRPCError } from '@trpc/server'

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
}).or(z.object({}))

const regulatoryRegionToGeneSchema = schema['regulatory element to gene expression association']

async function findPredictionsFromGene (input: paramsFormatType): Promise<any> {
  if (input.gene_id === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'gene_id must be specified.'
    })
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const query = `
    LET gene = (
      FOR geneRecord IN genes
      FILTER geneRecord._id == 'genes/${input.gene_id as string}'
      RETURN {
        name: geneRecord.name,
        id: geneRecord._id,
        start: geneRecord['start:long'],
        end: geneRecord['end:long'],
        chr: geneRecord.chr
      }
    )[0]

    LET predictions = (
      FOR record IN ${regulatoryRegionToGeneSchema.db_collection_name as string}
      FILTER record._to == 'genes/${input.gene_id as string}'
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
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
    )

    RETURN (gene != NULL ? { 'gene': gene, 'predictions': predictions }: {})
  `

  return (await (await db.query(query)).all())[0]
}

const regulatoryRegionsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/predictions', description: descriptions.genes_predictions } })
  .input(z.object({ gene_id: z.string() }).merge(commonNodesParamsFormat).omit({ organism: true }))
  .output(predictionFromGeneFormat)
  .query(async ({ input }) => await findPredictionsFromGene(input))

export const genesRegulatoryRegionsRouters = {
  regulatoryRegionsFromGenes
}
