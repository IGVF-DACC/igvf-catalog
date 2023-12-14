import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { geneFormat, genesQueryFormat } from '../nodes/genes'
import { paramsFormatType } from '../_helpers'
import { regulatoryRegionFormat, regulatoryRegionsQueryFormat } from '../nodes/regulatory_regions'
import { descriptions } from '../descriptions'

const edgeSources = z.object({
  source: z.enum([
    'ENCODE_EpiRaction',
    'ENCODE-E2G-DNaseOnly',
    'ENCODE-E2G-Full'
  ]).optional()
})

function edgeQuery (input: paramsFormatType): string {
  const query = []

  if (input.source !== undefined) {
    query.push(`record.source == '${input.source}'`)
    delete input.source
  }

  return query.join('and ')
}

const schema = loadSchemaConfig()

const regulatoryRegionToGeneFormat = z.object({
  score: z.number().nullable(),
  source: z.string().optional(),
  source_url: z.string().optional(),
  'regulatory region': z.string().or(z.array(regulatoryRegionFormat)).optional(),
  gene: z.string().or(z.array(geneFormat)).optional(),
  term_name: z.string().nullable() // the NTR terms from ENCODE need to be added to ontology terms collection
})
const schemaObj = schema['regulatory element to gene expression association']
const router = new RouterEdges(schemaObj)

async function conditionalGeneSearch (input: paramsFormatType): Promise<any[]> {
  if (input.gene_id !== undefined) {
    input._id = `genes/${input.gene_id}`
    delete input.gene_id
  }

  return await router.getSourcesWithVerboseProp(input, '_key', input.verbose === 'true', edgeQuery(input), 'biological_context', 'term_name')
}

const regulatoryRegionsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/regulatory_regions', description: descriptions.genes_regulatory_regions } })
  .input(genesQueryFormat.merge(edgeSources).merge(z.object({ verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(regulatoryRegionToGeneFormat))
  .query(async ({ input }) => await conditionalGeneSearch(input))

const genesFromRegulatoryRegions = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/regulatory_regions/genes', description: descriptions.regulatory_regions_genes } })
  .input(regulatoryRegionsQueryFormat.merge(edgeSources).merge(z.object({ verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(regulatoryRegionToGeneFormat))
  .query(async ({ input }) => await router.getTargetsWithVerboseProp(input, '_key', input.verbose === 'true', edgeQuery(input), 'biological_context', 'term_name'))

export const regulatoryRegionsGenesRouters = {
  regulatoryRegionsFromGenes,
  genesFromRegulatoryRegions
}
