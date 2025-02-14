import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { commonNodesParamsFormat } from '../params'
import { TRPCError } from '@trpc/server'
import { findTranscriptsFromProteinSearch } from '../edges/transcripts_proteins'

const MAX_PAGE_SIZE = 500
const REGION_IDX = 'idx_region'

const schema = loadSchemaConfig()
const QueryFormat = z.object({
  gene_id: z.string().trim().optional(),
  gene_name: z.string().trim().optional(),
  transcript_id: z.string().trim().optional(),
  transcript_name: z.string().trim().optional(),
  protein_id: z.string().trim().optional(),
  protein_name: z.string().trim().optional(),
  region: z.string().trim().optional()
}).merge(commonNodesParamsFormat)

const GeneStructureFormat = z.object({
  _id: z.string(),
  name: z.string(),
  chr: z.string(),
  start: z.number().nullable(),
  end: z.number().nullable(),
  strand: z.string(),
  type: z.string(),
  gene_id: z.string(),
  gene_name: z.string(),
  transcript_id: z.string(),
  transcript_name: z.string(),
  protein_id: z.string().nullish(),
  exon_number: z.string(),
  exon_id: z.string().nullable(),
  organism: z.string(),
  source: z.string(),
  version: z.string(),
  source_url: z.string()
})

let genesStructureSchema = schema['gene structure']

function validateInput (fromGene: boolean, fromTranscript: boolean, fromProtein: boolean, fromRegion: boolean): void {
  // count the number of parameters that are defined
  const numParams = [fromGene, fromTranscript, fromProtein, fromRegion].filter(item => item).length
  if (numParams > 1) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Please provide parameters from only one of the four categories: gene, transcript, protein or region'
    })
  }
}

export async function geneStructureSearch (input: paramsFormatType): Promise<any[]> {
  let useIndex = ''
  if (input.region !== undefined) {
    useIndex = `OPTIONS { indexHint: "${REGION_IDX}", forceIndexHint: true }`
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  const page = input.page ?? 0
  delete input.page
  if (input.organism === 'Mus musculus') {
    genesStructureSchema = schema['mouse gene structure']
  }
  let fromGene = false
  let fromTranscript = false
  let fromProtein = false
  let fromRegion = false
  for (const key in input) {
    if (input[key] !== undefined) {
      if (key === 'gene_id' || key === 'gene_name') {
        fromGene = true
      } else if (key === 'transcript_id' || key === 'transcript_name') {
        fromTranscript = true
      } else if (key === 'protein_id' || key === 'protein_name') {
        fromProtein = true
      } else if (key === 'region') {
        fromRegion = true
      }
    }
  }
  validateInput(fromGene, fromTranscript, fromProtein, fromRegion)
  const preProcessed = preProcessRegionParam(input)
  let filterBy = ''
  const filterSts = getFilterStatements(genesStructureSchema, preProcessed)
  if (filterSts !== '') {
    filterBy = `FILTER ${filterSts}`
  }
  if (!fromProtein) {
    const query = `
      FOR record in ${genesStructureSchema.db_collection_name as string} ${useIndex}
      ${filterBy}
      SORT record.gene_id, record.transcript_id, record.start
      LIMIT ${page as number * limit}, ${limit}
      RETURN {${getDBReturnStatements(genesStructureSchema)}}
    `
    return await (await db.query(query)).all()
  } else {
    const proteinInput = {
      protein_id: input.protein_id,
      protein_name: input.protein_name,
      organism: input.organism,
      page: 0
    }
    const proteinsTranscripts = await findTranscriptsFromProteinSearch(proteinInput)
    const transcriptsList = proteinsTranscripts.map((item: any) => {
      return {
        transcript: item.transcript.split('/')[1],
        protein: item.protein.split('/')[1]
      }
    })
    const query = `
      FOR doc in ${JSON.stringify(transcriptsList)}
      FOR record in ${genesStructureSchema.db_collection_name as string} ${useIndex}
      filter record.transcript_id == doc.transcript
      SORT record.gene_id, record.transcript_id, record.start
      LIMIT ${page as number * limit}, ${limit}
      RETURN {
        'protein_id': doc.protein,
      ${getDBReturnStatements(genesStructureSchema)}}
    `
    return await (await db.query(query)).all()
  }
}

const genesStructure = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes-structure', description: descriptions.genes_structure } })
  .input(QueryFormat)
  .output(z.array(GeneStructureFormat))
  .query(async ({ input }) => await geneStructureSearch(input))

export const genesStructureRouters = {
  genesStructure
}
