import { motifsProteinsRouters, motifsToProteinsFormat } from '../../../datatypeRouters/edges/motifs_proteins'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// motifs_proteins is fed by 2 structurally different methods (HOCOMOCO vs SEMpl motif
// prediction) - loop over both so a format-specific regression can't hide behind the other
// method's passing rows.
describe('motifsProteinsRouters.proteinsFromMotifs (integration)', () => {
  // tf_name is backed by a persistent index on the motifs collection (confirmed via
  // db.explain - no full collection scan), so this is an exact-match indexed point lookup,
  // not a free-text/fuzzy search.
  const cases: Array<{ method: string, tf_name: string }> = [
    { method: 'SEMpl', tf_name: 'EGR1' },
    { method: 'HOCOMOCO', tf_name: 'AHR_HUMAN' }
  ]

  it.each(cases)('returns schema-valid $method targets for a real TF motif', async (testCase) => {
    const input = { tf_name: testCase.tf_name, method: testCase.method, page: 0, limit: 10 }
    const result: any = await motifsProteinsRouters.proteinsFromMotifs({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = motifsToProteinsFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.method} record ${JSON.stringify(record)}: ${parsed.error.toString()}`)
      }
    }
  })
})

describe('motifsProteinsRouters.motifsFromProteins (integration)', () => {
  const cases: Array<{ method: string, protein_id: string }> = [
    { method: 'SEMpl', protein_id: 'ENSP00000239938' },
    { method: 'HOCOMOCO', protein_id: 'ENSP00000242057' }
  ]

  it.each(cases)('returns schema-valid $method motifs for a real protein', async (testCase) => {
    const input = { protein_id: testCase.protein_id, method: testCase.method, page: 0, limit: 10 }
    const result: any = await motifsProteinsRouters.motifsFromProteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = motifsToProteinsFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.method} record ${JSON.stringify(record)}: ${parsed.error.toString()}`)
      }
    }
  })
})
