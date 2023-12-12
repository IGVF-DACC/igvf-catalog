import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { TRPCError } from '@trpc/server'
import { proteinFormat } from '../nodes/proteins'
import { descriptions } from '../descriptions'
import { paramsFormatType } from '../_helpers'

const schema = loadSchemaConfig()

const schemaObj = schema['protein to protein interaction']

const routerEdge = new RouterEdges(schemaObj)

const sources = z.enum(['IntAct', 'BioGRID', 'BioGRID; IntAct'])

function edgeQuery (input: paramsFormatType): string {
  const query = []

  if (input.pmid !== undefined && input.pmid !== '') {
    const pmidUrl = 'http://pubmed.ncbi.nlm.nih.gov/'
    input.pmid = pmidUrl + (input.pmid as string)
    query.push(`'${input.pmid}' IN record.pmids`)
    delete input.pmid
  }

  if (input.source !== undefined) {
    query.push(`record.source == '${input.source}'`)
    delete input.source
  }

  if (input['interaction type'] !== undefined) {
    query.push(`record.interaction_type == '${input['interaction type']}'`)
    delete input['interaction type']
  }

  if (input['detection method'] !== undefined) {
    query.push(`record.detection_method == '${input['detection method']}'`)
    delete input['detection method']
  }

  if (Object.keys(input).filter(item => !['page', 'verbose'].includes(item)).length === 0) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one protein property must be defined.'
    })
  }

  return query.join(' and ')
}

async function conditionalProteinSearch (input: paramsFormatType): Promise<any[]> {
  if (input.protein_id !== undefined) {
    input._id = `proteins/${input.protein_id as string}`
    delete input.protein_id
  }
  return await routerEdge.getBidirectionalByNode(input, '_key', edgeQuery(input), input.verbose === 'true')
}

const proteinsProteinsQueryFormat = z.object({
  protein_id: z.string().trim().optional(),
  name: z.string().trim().optional(),
  'detection method': z.string().trim().optional(),
  'interaction type': z.string().trim().optional(),
  pmid: z.string().trim().optional(),
  source: sources.optional(),
  page: z.number().default(0),
  verbose: z.enum(['true', 'false']).default('false')
})

const proteinsProteinsFormat = z.object({
  // ignore dbxrefs field to avoid long output
  'protein 1': z.string().or(z.array(proteinFormat.omit({ dbxrefs: true }))),
  'protein 2': z.string().or(z.array(proteinFormat.omit({ dbxrefs: true }))),
  detection_method: z.string(),
  detection_method_code: z.string(),
  interaction_type: z.string(),
  interaction_type_code: z.string(),
  confidence_values: z.array(z.string()),
  source: z.string(),
  pmids: z.array(z.string())
})

const proteinsProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/proteins', description: descriptions.proteins_proteins } })
  .input(proteinsProteinsQueryFormat)
  .output(z.array(proteinsProteinsFormat))
  .query(async ({ input }) => await conditionalProteinSearch(input))

export const proteinsProteinsRouters = {
  proteinsProteins
}
