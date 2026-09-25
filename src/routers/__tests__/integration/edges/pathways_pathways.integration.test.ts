import { pathwaysPathwaysRouters, pathwaysPathwaysFormat } from '../../../datatypeRouters/edges/pathways_pathways'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
describe('pathwaysPathwaysRouters.pathwaysFromPathways (integration)', () => {
  it('returns schema-valid pathway-pathway relationships for a real pathway', async () => {
    // pathways/R-HSA-109581 --parent of--> pathways/R-HSA-109606
    const input = { pathway_id: 'R-HSA-109606', organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await pathwaysPathwaysRouters.pathwaysFromPathways({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = pathwaysPathwaysFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for record ${JSON.stringify(record)}: ${parsed.error.toString()}`)
      }
    }
  })
})
