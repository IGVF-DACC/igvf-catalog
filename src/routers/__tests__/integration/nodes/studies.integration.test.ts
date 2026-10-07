import { studiesRouters, studyFormat } from '../../../datatypeRouters/nodes/studies'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// studies has a single exported procedure, backed by a plain FILTER/LIMIT query (no cascade,
// no per-row sub-queries). `study_id` maps to a `record._key == X` filter, optimized via the
// primary index. `pmid` and `files_fileset` have no dedicated index, but the `studies`
// collection only holds ~22.7k documents, so a full scan there is negligible - unlike the
// billion-row `variants`/`genes_genes`-scale collections this constraint is guarding against.
describe('studiesRouters.studies (integration)', () => {
  const cases: Array<{ label: string, input: Record<string, string | number> }> = [
    { label: 'study_id', input: { study_id: 'GCST004365_80' } },
    { label: 'pmid', input: { pmid: '28240269' } },
    { label: 'files_fileset', input: { files_fileset: 'IGVFFI1309WDQG' } }
  ]

  it.each(cases)('returns schema-valid records filtered by $label', async (testCase) => {
    const result: any = await studiesRouters.studies({
      input: testCase.input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: testCase.input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = studyFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.label} record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })
})
