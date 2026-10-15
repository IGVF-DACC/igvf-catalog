import { genesGenesEdgeRouters, genesGenesRelativeFormat } from '../../../datatypeRouters/edges/genes_genes'
import { db } from '../../../../database'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// genes_genes holds two structurally different sources (BioGRID vs COXPRESdb, e.g. z_score
// only ever appears on COXPRESdb edges) - test each source against real data so a schema
// drift specific to one source's shape can't hide behind the other's passing rows.
describe('genesGenesEdgeRouters.genesGenes (integration)', () => {
  const cases: Array<{ source: string, gene_id: string }> = [
    { source: 'BioGRID', gene_id: 'ENSG00000115875' },
    { source: 'COXPRESdb', gene_id: 'ENSG00000121410' }
  ]

  it.each(cases)('returns schema-valid $source edges for a real gene', async (testCase) => {
    const input = { gene_id: testCase.gene_id, organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await genesGenesEdgeRouters.genesGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    const matchingSource = result.filter((record: any) => record.source === testCase.source)
    expect(matchingSource.length).toBeGreaterThan(0)

    for (const record of matchingSource) {
      const parsed = genesGenesRelativeFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.source} record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })

  // `method` is a separate, more granular field than `source` here (BioGRID alone has ~30
  // distinct interaction-type method values, all sharing the same record shape as any other
  // BioGRID row) - the cases above only ever filtered by `source`, so `method` itself was
  // never exercised as a filter. One direct check per source is enough to cover the param
  // itself; looping every BioGRID method string wouldn't find any new shape.
  const methodCases: Array<{ method: string, gene_id: string }> = [
    { method: 'negative genetic interaction (sensu BioGRID)', gene_id: 'ENSG00000115875' },
    { method: 'COXPRESdb', gene_id: 'ENSG00000121410' }
  ]

  it.each(methodCases)('returns schema-valid edges filtered by method=$method', async (testCase) => {
    const input = { gene_id: testCase.gene_id, method: testCase.method, organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await genesGenesEdgeRouters.genesGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = genesGenesRelativeFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for method=${testCase.method} record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })

  // genes_genes has 2.2M+ COXPRESdb edges - a gene_id lookup that falls back to a full
  // collection scan would be expensive on every request, not just in this test.
  it('uses an index (not a full collection scan) for a gene_id lookup', async () => {
    const querySpy = jest.spyOn(db, 'query')

    const input = { gene_id: 'ENSG00000115875', organism: 'Homo sapiens', page: 0, limit: 10 }
    await genesGenesEdgeRouters.genesGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(querySpy).toHaveBeenCalled()
    const [capturedQuery] = querySpy.mock.calls[querySpy.mock.calls.length - 1]
    querySpy.mockRestore()

    const explanation = await db.explain(capturedQuery as any)
    const fullScans = explanation.plan.nodes.filter((node: any) => node.type === 'EnumerateCollectionNode')
    if (fullScans.length > 0) {
      throw new Error(`Query performs a full collection scan (no index used): ${JSON.stringify(fullScans, null, 2)}`)
    }
  })
})
