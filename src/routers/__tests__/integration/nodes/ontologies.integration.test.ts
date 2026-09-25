import { ontologyRouters, ontologyFormat } from '../../../datatypeRouters/nodes/ontologies'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// ontologySearch() runs exactMatchSearch() first, which is a single
// `FOR record IN ontology_terms FILTER ... LIMIT N` query. It only falls into the expensive
// prefixMatchSearch/fuzzyTextSearch cascade (TOKENS()/LEVENSHTEIN_MATCH() against a search
// view) when a bare `name` param is supplied and the exact match returns zero rows. We never
// pass `name` here, so every case below stays on the single cheap exactMatchSearch query -
// filtering by `term_id` (direct point lookup) or by the `source`/`subontology` enums alone.
describe('ontologyRouters.ontologyTerm (integration)', () => {
  it('returns schema-valid records for a direct term_id lookup', async () => {
    const input = { term_id: 'NTR_0001118', page: 0, limit: 10 }
    const result: any = await ontologyRouters.ontologyTerm({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = ontologyFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for record: ${parsed.error.toString()}`)
      }
    }
  })

  // Every real `source` enum value on the ontology_terms collection, discovered via a live
  // probe query (getCollectionEnumValuesOrThrow + a per-value FILTER probe) - all returned
  // at least one row except 'ENCODE', which currently has no loaded ontology_terms records.
  const sourceCases: Array<{ source: string }> = [
    { source: 'BAO' },
    { source: 'CHEBI' },
    { source: 'CL' },
    { source: 'CLO' },
    { source: 'Cellosaurus' },
    { source: 'DOID' },
    { source: 'EFO' },
    { source: 'GO' },
    { source: 'HPO' },
    { source: 'IGVF' },
    { source: 'MONDO' },
    { source: 'NCIT' },
    { source: 'OBA' },
    { source: 'OBI' },
    { source: 'ORPHANET' },
    { source: 'Oncotree' },
    { source: 'PCL' },
    { source: 'UBERON' },
    { source: 'VARIO' }
  ]

  it.each(sourceCases)('returns schema-valid records filtered by source=$source', async (testCase) => {
    const input = { source: testCase.source, page: 0, limit: 10 }
    const result: any = await ontologyRouters.ontologyTerm({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = ontologyFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for source=${testCase.source} record: ${parsed.error.toString()}`)
      }
    }
  })

  const subontologyCases: Array<{ subontology: string }> = [
    { subontology: 'biological_process' },
    { subontology: 'cellular_component' },
    { subontology: 'molecular_function' }
  ]

  it.each(subontologyCases)('returns schema-valid records filtered by subontology=$subontology', async (testCase) => {
    const input = { subontology: testCase.subontology, page: 0, limit: 10 }
    const result: any = await ontologyRouters.ontologyTerm({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = ontologyFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for subontology=${testCase.subontology} record: ${parsed.error.toString()}`)
      }
    }
  })
})
