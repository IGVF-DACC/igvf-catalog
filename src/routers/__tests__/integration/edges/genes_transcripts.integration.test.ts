import { genesTranscriptsRouters, genesTranscriptsFormat, genesProteinsFormat } from '../../../datatypeRouters/edges/genes_transcripts'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// Sample IDs below all come from the same real gene -> transcript -> protein chain
// (genes/ENSG00000198836 -> transcripts/ENST00000361510 -> proteins/ENSP00000355324) so
// every procedure in this router is exercised against real, related data.
describe('genesTranscriptsRouters (integration)', () => {
  it('transcriptsFromGenes returns schema-valid transcripts for a real gene', async () => {
    const input = { gene_id: 'ENSG00000198836', organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await genesTranscriptsRouters.transcriptsFromGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = genesTranscriptsFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for transcriptsFromGenes record: ${parsed.error.toString()}`)
      }
    }
  })

  it('genesFromTranscripts returns schema-valid genes for a real transcript', async () => {
    const input = { transcript_id: 'ENST00000361510', organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await genesTranscriptsRouters.genesFromTranscripts({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = genesTranscriptsFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for genesFromTranscripts record: ${parsed.error.toString()}`)
      }
    }
  })

  it('proteinsFromGenes returns schema-valid proteins for a real gene', async () => {
    const input = { gene_id: 'ENSG00000198836', organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await genesTranscriptsRouters.proteinsFromGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = genesProteinsFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for proteinsFromGenes record: ${parsed.error.toString()}`)
      }
    }
  })

  it('genesFromProteins returns schema-valid genes for a real protein', async () => {
    const input = { protein_id: 'ENSP00000355324', organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await genesTranscriptsRouters.genesFromProteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = genesProteinsFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for genesFromProteins record: ${parsed.error.toString()}`)
      }
    }
  })
})
