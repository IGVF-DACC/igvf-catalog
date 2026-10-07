import { drugsRouters, drugFormat } from '../../../datatypeRouters/nodes/drugs'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// drugs has a single exported procedure. It supports a fast `drug_id` (_key) point lookup,
// but a bare `name` routes to a TOKENS() SEARCH-view query that falls back to a
// LEVENSHTEIN_MATCH fuzzy scan when the token match is empty - that expensive cascade is
// intentionally not exercised here per the integration-tier performance constraint (only
// ID-style filters).
describe('drugsRouters.drugs (integration)', () => {
  it('returns schema-valid records for a real drug_id', async () => {
    const input = { drug_id: 'PA166250381' }
    const result: any = await drugsRouters.drugs({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = drugFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })
})
