import { genomicElementsGenesRouters, outputFormat } from '../../../datatypeRouters/edges/genomic_elements_genes'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// This collection merges 4 distinct sources (CRISPR screen, ENCODE-rE2G, Perturb-seq, scE2G),
// each with different populated fields (e.g. z_score/idr only on some) - loop over all of
// them so a format-specific regression can't hide behind another method's passing rows.
describe('genomicElementsGenesRouters.genomicElementsFromGenes (integration)', () => {
  const cases: Array<{ method: string, gene_id: string }> = [
    { method: 'CRISPR screen', gene_id: 'ENSG00000160049' },
    { method: 'ENCODE-rE2G', gene_id: 'ENSG00000162444' },
    { method: 'Perturb-seq', gene_id: 'ENSG00000019582' },
    { method: 'scE2G', gene_id: 'ENSG00000156875' }
  ]

  it.each(cases)('returns schema-valid $method edges for a real gene', async (testCase) => {
    const input = { gene_id: testCase.gene_id, organism: 'Homo sapiens', method: testCase.method, page: 0, limit: 10 }
    const result: any = await genomicElementsGenesRouters.genomicElementsFromGenes({
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
        throw new Error(`Output validation failed for ${testCase.method} record: ${parsed.error.toString()}`)
      }
    }
  })
})
