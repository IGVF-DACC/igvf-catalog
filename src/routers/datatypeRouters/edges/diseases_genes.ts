import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { geneFormat, genesQueryFormat } from '../nodes/genes'
import { ontologyFormat } from '../nodes/ontologies'
import { paramsFormatType } from '../_helpers'
import { TRPCError } from '@trpc/server'
import { descriptions } from '../descriptions'

const associationTypes = z.object({
  association_type: z.enum([
    'Disease-causing germline mutation(s) in',
    'Modifying germline mutation in',
    'Major susceptibility factor in',
    'Candidate gene tested in',
    'Disease-causing germline mutation(s) (loss of function) in',
    'Disease-causing somatic mutation(s) in',
    'Disease-causing germline mutation(s) (gain of function) in',
    'Role in the phenotype of',
    'Part of a fusion gene in',
    'Biomarker tested in'
  ]).optional()
})

const schema = loadSchemaConfig()

const diseasesToGenesFormat = z.object({
  pmid: z.array(z.string()).optional(),
  term_name: z.string().optional(),
  gene_symbol: z.string().optional(),
  association_type: z.string().optional(),
  association_status: z.string().optional(),
  source: z.string().optional(),
  source_url: z.string().optional(),
  gene: z.string().or(z.array(geneFormat)).optional(),
  'ontology term': z.string().or(z.array(ontologyFormat)).optional()
})

const schemaObj = schema['disease to gene']
const router = new RouterEdges(schemaObj)

function edgeQuery (input: paramsFormatType): string {
  const query = []

  if (input.association_type !== undefined && input.association_type !== '') {
    query.push(`record.association_type == '${input.association_type}'`)
    delete input.association_type
  }

  if (input.source !== undefined && input.source !== '') {
    query.push(`record.source == '${input.source}'`)
    delete input.source
  }

  if (Object.keys(input).filter(item => !['page', 'verbose'].includes(item)).length === 0) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one gene property must be defined.'
    })
  }

  return query.join('and ')
}

const genesFromDiseaseID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/diseases/{disease_id}/genes', description: descriptions.diseases_id_genes } })
  .input(z.object({ disease_id: z.string(), page: z.number().default(0), verbose: z.enum(['true', 'false']).default('false') }))
  .output(z.array(diseasesToGenesFormat))
  .query(async ({ input }) => await router.getTargetsByID(input.disease_id, input.page, '_key', input.verbose === 'true'))

const diseasesFromGeneID = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/{gene_id}/diseases', description: descriptions.genes_id_diseases } })
  .input(z.object({ gene_id: z.string(), page: z.number().default(0), verbose: z.enum(['true', 'false']).default('false') }))
  .output(z.array(diseasesToGenesFormat))
  .query(async ({ input }) => await router.getSourcesByID(input.gene_id, input.page, '_key', input.verbose === 'true'))

const diseasesFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/diseases', description: descriptions.genes_diseases } })
  .input(genesQueryFormat.merge(associationTypes).merge(z.object({ source: z.string().optional(), page: z.number().default(0), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(diseasesToGenesFormat))
  .query(async ({ input }) => await router.getSources(input, '_key', input.verbose === 'true', edgeQuery(input)))

const genesFromDiseases = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/diseases/genes', description: descriptions.diseases_genes } })
  .input(associationTypes.merge(z.object({ term_name: z.string(), source: z.string().optional(), page: z.number().default(0), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(diseasesToGenesFormat))
  .query(async ({ input }) => await router.getTargetEdgesByAutocompleteSearch(input, 'term_name', input.verbose === 'true'))

export const diseasesGenesRouters = {
  genesFromDiseaseID,
  genesFromDiseases,
  diseasesFromGeneID,
  diseasesFromGenes
}
