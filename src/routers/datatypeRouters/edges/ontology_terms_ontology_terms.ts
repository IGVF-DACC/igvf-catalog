import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterTransitiveClosure } from '../../genericRouters/routerTransitiveClosure'
import { RouterGraph } from '../../genericRouters/routerGraph'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

const schemaObj = schema['ontology term']
const edgeSchemaObj = schema['ontology relationship']

const routerGraph = new RouterGraph(schemaObj)
const routerClosure = new RouterTransitiveClosure(edgeSchemaObj, 'ontology_terms')

const ontologyRelativeFormat = z.object({
  ontology_term_id: z.string(),
  relationship_type: z.string().nullable()
})

const ontologyTermChildren = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/ontology_terms/{ontology_term_id}/children', description: descriptions.ontology_terms_children } })
  .input(z.object({ ontology_term_id: z.string().trim() }))
  .output(z.array(ontologyRelativeFormat.optional()))
  .query(async ({ input }) => await routerGraph.getObjectByGraphQuery(input.ontology_term_id, 'ontology_terms_ontology_terms', 'children'))

const ontologyTermParents = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/ontology_terms/{ontology_term_id}/parents',description: descriptions.ontology_terms_parents } })
  .input(z.object({ ontology_term_id: z.string().trim() }))
  .output(z.array(ontologyRelativeFormat.optional()))
  .query(async ({ input }) => await routerGraph.getObjectByGraphQuery(input.ontology_term_id, 'ontology_terms_ontology_terms', 'parents'))

const ontologyTermTransitiveClosure = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/ontology_terms/{ontology_term_id_start}/transitive_closure/{ontology_term_id_end}', description: descriptions.ontology_terms_transitive_closure } })
  .input(z.object({ ontology_term_id_start: z.string().trim(), ontology_term_id_end: z.string().trim() }))
  .output(z.any())
  .query(async ({ input }) => await routerClosure.getPaths(input.ontology_term_id_start, input.ontology_term_id_end))

export const ontologyTermsEdgeRouters = {
  ontologyTermChildren,
  ontologyTermParents,
  ontologyTermTransitiveClosure
}
