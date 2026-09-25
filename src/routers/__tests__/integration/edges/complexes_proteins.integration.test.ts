import { complexesProteinsRouters, proteinComplexFormat } from '../../../datatypeRouters/edges/complexes_proteins'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// Both procedures below support a `verbose` flag that swaps the `protein`/`complex` fields
// from a bare _id string to a fully resolved node object via a separate DOCUMENT() lookup -
// a distinct code path from the default (non-verbose) shape, so both are exercised here.
describe('complexesProteinsRouters.complexesFromProteins (integration)', () => {
  const verboseCases = ['false', 'true']

  it.each(verboseCases)('returns schema-valid complexes for a real protein_id (verbose=%s)', async (verbose) => {
    const input = { protein_id: 'ENSP00000325970', organism: 'Homo sapiens', verbose, page: 0, limit: 5 }
    const result: any = await complexesProteinsRouters.complexesFromProteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = proteinComplexFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for record (verbose=${verbose}): ${parsed.error.toString()}`)
      }
    }
  })
})

describe('complexesProteinsRouters.proteinsFromComplexes (integration)', () => {
  const verboseCases = ['false', 'true']

  it.each(verboseCases)('returns schema-valid proteins for a real complex_id (verbose=%s)', async (verbose) => {
    const input = { complex_id: 'CPX-2004', organism: 'Homo sapiens', verbose, page: 0, limit: 5 }
    const result: any = await complexesProteinsRouters.proteinsFromComplexes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = proteinComplexFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for record (verbose=${verbose}): ${parsed.error.toString()}`)
      }
    }
  })
})
