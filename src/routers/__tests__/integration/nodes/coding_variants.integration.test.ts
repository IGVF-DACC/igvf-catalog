import { codingVariantsRouters, codingVariantsFormat } from '../../../datatypeRouters/nodes/coding_variants'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// codingVariants has no free-text/fuzzy fallback path at all (no TOKENS()/SEARCH view
// anywhere in this router) - every supported filter is a plain equality FILTER on a single
// collection, so any of its documented ID-style params is safe to exercise directly.
describe('codingVariantsRouters.codingVariants (integration)', () => {
  const cases: Array<{ label: string, input: Record<string, string | number> }> = [
    { label: 'id (_key)', input: { id: 'AFF2_ENST00000370460_p.Met1!_c.1_3delinsGCA', limit: 5 } },
    { label: 'protein_id', input: { protein_id: 'ENSP00000359489', limit: 5 } }
  ]

  it.each(cases)('returns schema-valid records filtered by $label', async (testCase) => {
    const result: any = await codingVariantsRouters.codingVariants({
      input: testCase.input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: testCase.input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = codingVariantsFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.label} record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })
})
