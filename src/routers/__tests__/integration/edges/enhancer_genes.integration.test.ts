import { enhancerGenePredictionsRouters, genesGenomicElementsOutputFormat } from '../../../datatypeRouters/edges/enhancer_genes'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// enhancer_genes reads from the same `genomic_elements_genes` collection as
// genomic_elements_genes.ts, scoped to just the 2 enhancer-gene-prediction methods
// (ENCODE-rE2G, scE2G) - loop over both so a format-specific regression in this router's own
// aggregation (COLLECT gene INTO rows) can't hide behind the other method's passing rows.
describe('enhancerGenePredictionsRouters.enhancerGenePredictions (integration)', () => {
  const cases: Array<{ method: string, gene_id: string }> = [
    { method: 'ENCODE-rE2G', gene_id: 'ENSG00000162444' },
    { method: 'scE2G', gene_id: 'ENSG00000156875' }
  ]

  it.each(cases)('returns schema-valid $method predictions for a real gene', async (testCase) => {
    const input = { gene_id: testCase.gene_id, method: testCase.method, organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await enhancerGenePredictionsRouters.enhancerGenePredictions({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    const parsed = genesGenomicElementsOutputFormat.safeParse(result)
    if (!parsed.success) {
      throw new Error(`Output validation failed for ${testCase.method} result: ${parsed.error.toString()}`)
    }
  })
})
