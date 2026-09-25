import { qtlsRouters, outputFormat } from '../../../datatypeRouters/edges/qtls'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// qtls fans out to 3 different edge collections depending on `method` (variants_genes for
// eQTL/spliceQTL, variants_proteins for pQTL, variants_genomic_elements for caQTL), each with
// distinct populated fields (e.g. intron_* only on spliceQTL, regulatory_type/gene_consequence
// only on pQTL) - loop over all 4 methods against a real gene_id so a format-specific
// regression can't hide behind another method's passing rows.
//
// All cases use gene_id (a single-value point filter on record._to / record.gene), which keeps
// each underlying query to a single indexed lookup + LIMIT. The caQTL case additionally does one
// bounded chr/start-end range scan over genomic_elements for the single requested gene - the same
// shape already exercised by the approved variants_genes.integration.test.ts (nearestGenes).
describe('qtlsRouters.qtls (integration)', () => {
  const cases: Array<{ method: string, gene_id: string }> = [
    { method: 'eQTL', gene_id: 'ENSG00000182534' },
    { method: 'spliceQTL', gene_id: 'ENSG00000163913' },
    { method: 'pQTL', gene_id: 'ENSG00000175164' },
    { method: 'caQTL', gene_id: 'ENSG00000156875' }
  ]

  it.each(cases)('returns schema-valid $method edges for a real gene', async (testCase) => {
    const input = { gene_id: testCase.gene_id, method: testCase.method, organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await qtlsRouters.qtls({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = outputFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.method} record: ${parsed.error.toString()}`)
      }
      expect(record.method).toBe(testCase.method)
    }
  })
})
