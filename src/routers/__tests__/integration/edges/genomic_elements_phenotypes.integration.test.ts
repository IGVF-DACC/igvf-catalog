import { genomicElementsPhenotypesRouters, outputFormat } from '../../../datatypeRouters/edges/genomic_elements_phenotypes'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// Both procedures are queried by `phenotype_id` (a direct ontology_terms ID, resolved with no
// extra DB round-trip) plus `method`, never `region` or `phenotype_name` (which would add a
// region-intersection query / a free-text name lookup respectively) - so this stays a single
// filtered, limited scan of genomic_elements_phenotypes.
describe('genomicElementsPhenotypesRouters (integration)', () => {
  it('phenotypesFromGenomicElements returns schema-valid edges for a real phenotype', async () => {
    const input = { phenotype_id: 'GO_0016477', method: 'CRISPR screen', organism: 'Homo sapiens', verbose: 'false', page: 0, limit: 10 }
    const result: any = await genomicElementsPhenotypesRouters.phenotypesFromGenomicElements({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = outputFormat.element.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for phenotypesFromGenomicElements record: ${parsed.error.toString()}`)
      }
    }
  })

  it('genomicElementsFromPhenotypes returns schema-valid edges for a real phenotype', async () => {
    const input = { phenotype_id: 'GO_0016477', method: 'CRISPR screen', organism: 'Homo sapiens', verbose: 'false', page: 0, limit: 10 }
    const result: any = await genomicElementsPhenotypesRouters.genomicElementsFromPhenotypes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = outputFormat.element.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for genomicElementsFromPhenotypes record: ${parsed.error.toString()}`)
      }
    }
  })
})
