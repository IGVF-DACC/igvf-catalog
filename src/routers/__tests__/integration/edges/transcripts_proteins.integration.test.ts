import { transcriptsProteinsRouters, proteinTranscriptFormat } from '../../../datatypeRouters/edges/transcripts_proteins'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// Both procedures resolve via a single-value point filter (transcript_id -> record._key,
// protein_id -> record._key/protein_id/uniprot_ids) before joining transcripts_proteins on the
// indexed _from/_to, so each query stays a single indexed lookup + LIMIT. `verbose` swaps the
// `protein`/`transcript` field between a plain id string and the full nested node object, so we
// exercise both shapes since they are structurally different outputs.
describe('transcriptsProteinsRouters.proteinsFromTranscripts (integration)', () => {
  const cases: Array<{ verbose: 'true' | 'false' }> = [
    { verbose: 'false' },
    { verbose: 'true' }
  ]

  it.each(cases)('returns schema-valid edges for a real transcript (verbose=$verbose)', async (testCase) => {
    const input = { transcript_id: 'ENST00000361510', organism: 'Homo sapiens', verbose: testCase.verbose, page: 0, limit: 5 }
    const result: any = await transcriptsProteinsRouters.proteinsFromTranscripts({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = proteinTranscriptFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for record (verbose=${testCase.verbose}): ${parsed.error.toString()}`)
      }
    }
  })
})

describe('transcriptsProteinsRouters.transcriptsFromProteins (integration)', () => {
  const cases: Array<{ verbose: 'true' | 'false' }> = [
    { verbose: 'false' },
    { verbose: 'true' }
  ]

  it.each(cases)('returns schema-valid edges for a real protein (verbose=$verbose)', async (testCase) => {
    const input = { protein_id: 'ENSP00000355324', organism: 'Homo sapiens', verbose: testCase.verbose, page: 0, limit: 5 }
    const result: any = await transcriptsProteinsRouters.transcriptsFromProteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = proteinTranscriptFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for record (verbose=${testCase.verbose}): ${parsed.error.toString()}`)
      }
    }
  })
})
