import { variantsGenesRouters } from '../../../datatypeRouters/edges/variants_genes'
import { geneFormat } from '../../../datatypeRouters/nodes/genes'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
describe('variantsGenesRouters.nearestGenes (integration)', () => {
  it('returns schema-valid coding-region genes for a real region', async () => {
    const input = { region: 'chr1:33306765-33321098' }
    const result: any = await variantsGenesRouters.nearestGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = geneFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for gene record: ${parsed.error.toString()}`)
      }
    }
  })
})
