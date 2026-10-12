import { motifsRouters, motifFormat } from '../../../datatypeRouters/nodes/motifs'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// motifSearch() is a single `FOR record IN motifs FILTER ... LIMIT N` query with no fallback
// cascade, so filtering by the `method` or `source` enum alone is a safe, cheap point lookup.
describe('motifsRouters.motifs (integration)', () => {
  const methodCases: Array<{ method: string }> = [
    { method: 'HOCOMOCO' },
    { method: 'SEMpl' }
  ]

  it.each(methodCases)('returns schema-valid records filtered by method=$method', async (testCase) => {
    const input = { method: testCase.method, organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await motifsRouters.motifs({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = motifFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for method=${testCase.method} record: ${parsed.error.toString()}`)
      }
    }
  })

  const sourceCases: Array<{ source: string }> = [
    { source: 'IGVF' },
    { source: 'HOCOMOCOv11' }
  ]

  it.each(sourceCases)('returns schema-valid records filtered by source=$source', async (testCase) => {
    const input = { source: testCase.source, organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await motifsRouters.motifs({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = motifFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for source=${testCase.source} record: ${parsed.error.toString()}`)
      }
    }
  })
})
