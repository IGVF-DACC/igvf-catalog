import { genomicElementsBiosamplesRouters, genomicElementsToBiosampleFormat } from '../../../datatypeRouters/edges/genomic_elements_biosamples'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// Both procedures are queried by `method`/`source` (direct enum-equality filters on the edge
// collection itself) rather than a region or biosample-name lookup, so no upstream node search
// (and no region-intersection logic) is exercised - just a single filtered, limited scan of
// genomic_elements_biosamples. `source` is looped over both real values (ENCODE, IGVF) since
// it is an enum param on the edge, even though on this data both currently share the same
// populated-field shape.
describe('genomicElementsBiosamplesRouters (integration)', () => {
  const sources = ['ENCODE', 'IGVF']

  it.each(sources)('biosamplesFromGenomicElements returns schema-valid edges for source=%s', async (source) => {
    const input = { method: 'MPRA', source, organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await genomicElementsBiosamplesRouters.biosamplesFromGenomicElements({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = genomicElementsToBiosampleFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for biosamplesFromGenomicElements (${source}) record: ${parsed.error.toString()}`)
      }
    }
  })

  it.each(sources)('genomicElementsFromBiosamples returns schema-valid edges for source=%s', async (source) => {
    const input = { method: 'MPRA', source, organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await genomicElementsBiosamplesRouters.genomicElementsFromBiosamples({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = genomicElementsToBiosampleFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for genomicElementsFromBiosamples (${source}) record: ${parsed.error.toString()}`)
      }
    }
  })
})
