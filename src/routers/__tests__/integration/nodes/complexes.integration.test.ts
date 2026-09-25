import { complexesRouters, complexFormat } from '../../../datatypeRouters/nodes/complexes'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// complexes has a single exported procedure. It supports a fast `complex_id` (_key) point
// lookup, but `name`/`description` route to a TOKENS() SEARCH-view query against
// complexes_text_en_no_stem_inverted_search_alias - that fuzzy path is intentionally not
// exercised here per the integration-tier performance constraint (only ID-style filters).
describe('complexesRouters.complexes (integration)', () => {
  it('returns schema-valid records for a real complex_id', async () => {
    const input = { complex_id: 'SEMpl_AHR:ARNT:HIF1A' }
    const result: any = await complexesRouters.complexes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = complexFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })
})
