import { ontologyTermsEdgeRouters, ontologyRelativeFormat } from '../../../datatypeRouters/edges/ontology_terms_ontology_terms'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
//
// `ontologyTermTransitiveClosure` is intentionally NOT tested here. It runs an unbounded
// `ANY ALL_SHORTEST_PATHS` graph traversal (no depth limit) between two arbitrary ontology
// terms. Verified directly against the real dev DB: even a directly-adjacent (1-hop) pair
// took ~1s, and a pair with no real relationship (forcing the traversal to exhaust the
// reachable search space) hit a 504 Gateway Timeout. There's no bounded/indexed point-lookup
// shape available for this procedure.
describe('ontologyTermsEdgeRouters.ontologyTermChildren (integration)', () => {
  it('returns schema-valid children for a real ontology term', async () => {
    // ontology_terms/CHEBI_118579 --subclass--> ontology_terms/CHEBI_47857
    const input = { ontology_term_id: 'CHEBI_47857', page: 0, limit: 10 }
    const result: any = await ontologyTermsEdgeRouters.ontologyTermChildren({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = ontologyRelativeFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for record ${JSON.stringify(record)}: ${parsed.error.toString()}`)
      }
    }
  })
})

describe('ontologyTermsEdgeRouters.ontologyTermParents (integration)', () => {
  it('returns schema-valid parents for a real ontology term', async () => {
    // ontology_terms/CHEBI_118579 --subclass--> ontology_terms/CHEBI_47857
    const input = { ontology_term_id: 'CHEBI_118579', page: 0, limit: 10 }
    const result: any = await ontologyTermsEdgeRouters.ontologyTermParents({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = ontologyRelativeFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for record ${JSON.stringify(record)}: ${parsed.error.toString()}`)
      }
    }
  })
})
