import { proteinsProteinsRouters, proteinsProteinsFormat } from '../../../datatypeRouters/edges/proteins_proteins'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// proteins_proteins holds edges from 2 structurally distinct sources (BioGRID vs IntAct) -
// loop over both so a source-specific schema drift can't hide behind the other source's
// passing rows.
describe('proteinsProteinsRouters.proteinsProteins (integration)', () => {
  const cases: Array<{ source: string, protein_id: string }> = [
    { source: 'BioGRID', protein_id: 'ENSP00000396786' },
    { source: 'IntAct', protein_id: 'ENSP00000389716' }
  ]

  it.each(cases)('returns schema-valid $source interactions for a real protein', async (testCase) => {
    const input = { protein_id: testCase.protein_id, source: testCase.source, organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await proteinsProteinsRouters.proteinsProteins({
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
      const parsed = proteinsProteinsFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.source} record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })
})
