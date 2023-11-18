import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterTransitiveClosure } from '../../genericRouters/routerTransitiveClosure'
import { descriptions } from '../descriptions'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { ontologyFormat } from '../nodes/ontologies'

const schema = loadSchemaConfig()

const edgeSchemaObj = schema['ontology relationship']

const router = new RouterEdges(edgeSchemaObj)
const routerClosure = new RouterTransitiveClosure(edgeSchemaObj, 'ontology_terms')

const ontologyRelativeFormat = z.object({
  term: ontologyFormat,
  relationship_type: z.string().nullable()
})

const ontologyRelativeQueryFormat = z.object({
  ontology_term_id: z.string().trim(),
  page: z.number().default(0)
})

const ontologyTermChildren = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/ontology_terms/{ontology_term_id}/children', description: descriptions.ontology_terms_children } })
  .input(ontologyRelativeQueryFormat)
  .output(z.array(ontologyRelativeFormat.optional()))
  .query(async ({ input }) => await router.getChildrenParents(input.ontology_term_id, 'children', '_key', input.page))

const ontologyTermParents = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/ontology_terms/{ontology_term_id}/parents', description: descriptions.ontology_terms_parents } })
  .input(ontologyRelativeQueryFormat)
  .output(z.array(ontologyRelativeFormat.optional()))
  .query(async ({ input }) => await router.getChildrenParents(input.ontology_term_id, 'parents', '_key', input.page))

const ontologyTermTransitiveClosure = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/ontology_terms/{ontology_term_id_start}/transitive_closure/{ontology_term_id_end}', description: descriptions.ontology_terms_transitive_closure } })
  .input(z.object({ ontology_term_id_start: z.string().trim(), ontology_term_id_end: z.string().trim() }))
  .output(z.any())
  .query(async ({ input }) => await routerClosure.getPaths(input.ontology_term_id_start, input.ontology_term_id_end, Object.keys(ontologyFormat.shape)))

export const ontologyTermsEdgeRouters = {
  ontologyTermChildren,
  ontologyTermParents,
  ontologyTermTransitiveClosure
}
