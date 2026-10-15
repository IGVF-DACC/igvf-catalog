import { transcriptsRouters, transcriptFormat } from '../../../datatypeRouters/nodes/transcripts'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// transcripts has a single exported procedure. A `transcript_id` resolves to findTranscriptByID,
// a plain `record._key == X` filter (primary-index lookup) against either the `transcripts`
// (Homo sapiens) or `mm_transcripts` (Mus musculus) collection - cheap and index-backed. Note
// findTranscriptByID only matches against `_key` (the bare Ensembl ID, no version suffix), not
// the versioned `transcript_id` field, so the param value passed must be the bare _key form.
// Region or other-filter based lookups (findTranscripts) are not exercised here since
// transcript_id alone already covers the procedure's logic branch selection (organism -> schema).
describe('transcriptsRouters.transcripts (integration)', () => {
  const cases: Array<{ label: string, input: Record<string, string | number> }> = [
    { label: 'transcript_id (human)', input: { transcript_id: 'ENST00000456328', limit: 5 } },
    { label: 'transcript_id (mouse)', input: { transcript_id: 'ENSMUST00000193812', organism: 'Mus musculus', limit: 5 } }
  ]

  it.each(cases)('returns schema-valid records filtered by $label', async (testCase) => {
    const result: any = await transcriptsRouters.transcripts({
      input: testCase.input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: testCase.input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = transcriptFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.label} record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })
})
