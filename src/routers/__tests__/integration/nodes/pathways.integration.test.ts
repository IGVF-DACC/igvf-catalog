import { pathwaysRouters, pathwayFormat } from '../../../datatypeRouters/nodes/pathways'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// pathwaySearch() tries pathwaySearchPersistent() first, a single
// `FOR record IN pathways FILTER ... LIMIT N` query keyed directly off `_key` (via the `id`
// param) or other direct fields. It only falls into findPathwaysByTextSearch() (TOKENS()/
// LEVENSHTEIN_MATCH() against a search view) when `name`/`name_aliases` is supplied and the
// persistent lookup returns zero rows. We only use the direct `id` (_key) filter here, so the
// text-search cascade is never exercised.
describe('pathwaysRouters.pathways (integration)', () => {
  const cases: Array<{ id: string }> = [
    { id: 'R-HSA-164843' },
    { id: 'R-HSA-9909438' }
  ]

  it.each(cases)('returns schema-valid records for a direct id lookup ($id)', async (testCase) => {
    const input = { id: testCase.id, organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await pathwaysRouters.pathways({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = pathwayFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for id=${testCase.id} record: ${parsed.error.toString()}`)
      }
    }
  })
})
