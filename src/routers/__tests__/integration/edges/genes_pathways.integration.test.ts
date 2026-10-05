import { genesPathwaysRouters, genesPathwaysFormat } from '../../../datatypeRouters/edges/genes_pathways'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
describe('genesPathwaysRouters (integration)', () => {
  it('pathwaysFromGenes returns schema-valid pathways for a real gene', async () => {
    const input = { gene_id: 'ENSG00000102882', organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await genesPathwaysRouters.pathwaysFromGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = genesPathwaysFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for pathwaysFromGenes record: ${parsed.error.toString()}`)
      }
    }
  })

  it('genesFromPathways returns schema-valid genes for a real pathway', async () => {
    const input = { pathway_id: 'R-HSA-5675221', organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await genesPathwaysRouters.genesFromPathways({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = genesPathwaysFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for genesFromPathways record: ${parsed.error.toString()}`)
      }
    }
  })
})
