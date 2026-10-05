import { proteinsRouters, proteinFormat } from '../../../datatypeRouters/nodes/proteins'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// proteins has a single exported procedure. It branches on which query params are present:
// `protein_id` resolves to findProteinByID, a single FILTER (record._key == X OR
// record.protein_id == X OR X IN record.uniprot_ids) confirmed via db.explain() to compile to
// an IndexNode (no EnumerateCollectionNode) - cheap and safe. Any of `name`/`uniprot_name`/
// `uniprot_full_name`/`dbxrefs` instead route to findProteinsByTextSearch, an exact -> prefix
// (STARTS_WITH/TOKENS) -> fuzzy (LEVENSHTEIN_MATCH) cascade against a search view - that path
// is intentionally never exercised here per the integration-tier performance constraint.
describe('proteinsRouters.proteins (integration)', () => {
  const cases: Array<{ label: string, input: Record<string, string | number> }> = [
    { label: 'protein_id (with version suffix)', input: { protein_id: 'ENSP00000493376.2', limit: 5 } },
    { label: 'protein_id (bare _key form)', input: { protein_id: 'ENSP00000493376', limit: 5 } }
  ]

  it.each(cases)('returns schema-valid records filtered by $label', async (testCase) => {
    const result: any = await proteinsRouters.proteins({
      input: testCase.input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: testCase.input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = proteinFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.label} record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })
})
