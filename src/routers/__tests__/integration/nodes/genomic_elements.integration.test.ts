import { genomicRegionsRouters, genomicElementFormat } from '../../../datatypeRouters/nodes/genomic_elements'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// genomicElementSearch() is a single `FOR record IN genomic_elements FILTER ... LIMIT N` query
// with no fallback cascade, so any single indexed-style filter (method/source) is safe here.
//
// The `method` enum includes 'integrative', whose underlying data source (FUNCODE) was never
// loaded into this dev DB - a probe query for method == 'integrative' (and source == 'FUNCODE')
// returned zero rows, so those two enum values are intentionally excluded from the loops below.
describe('genomicRegionsRouters.genomicElements (integration)', () => {
  const methodCases: Array<{ method: string }> = [
    { method: 'CRISPR screen' },
    { method: 'ENCODE-rE2G' },
    { method: 'MPRA' },
    { method: 'Perturb-seq' },
    { method: 'caQTL' },
    { method: 'candidate Cis-Regulatory Elements' },
    { method: 'scE2G' }
  ]

  it.each(methodCases)('returns schema-valid records filtered by method=$method', async (testCase) => {
    const input = { method: testCase.method, organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await genomicRegionsRouters.genomicElements({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = genomicElementFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for method=${testCase.method} record: ${parsed.error.toString()}`)
      }
    }
  })

  const sourceCases: Array<{ source: string }> = [
    { source: 'AFGR' },
    { source: 'ENCODE' },
    { source: 'IGVF' }
  ]

  it.each(sourceCases)('returns schema-valid records filtered by source=$source', async (testCase) => {
    const input = { source: testCase.source, organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await genomicRegionsRouters.genomicElements({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = genomicElementFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for source=${testCase.source} record: ${parsed.error.toString()}`)
      }
    }
  })
})
