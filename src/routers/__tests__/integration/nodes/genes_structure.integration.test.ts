import { genesStructureRouters, GeneStructureFormat } from '../../../datatypeRouters/nodes/genes_structure'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// geneStructureSearch() has two paths: a single-query direct filter (gene_id/gene_name/
// transcript_id/transcript_name/region) and a protein-driven path that first resolves
// transcripts via findTranscriptsFromProteinSearch() (an extra DB round trip) before
// querying genes_structure. We only exercise the direct gene_id/transcript_id filter path
// here - it is the single `FOR record IN genes_structure FILTER ... LIMIT N` query the
// resolver runs with no fallback cascade. The protein_id/protein_name path is skipped since
// it always performs a second DB call regardless of input, which is outside the cheap
// point-lookup scope of this test tier.
describe('genesStructureRouters.genesStructure (integration)', () => {
  const gene = { gene_id: 'ENSG00000290825' }
  const geneAlt = { gene_id: 'ENSG00000186092' }

  it('returns schema-valid records for a direct gene_id lookup', async () => {
    const input = { gene_id: gene.gene_id, organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await genesStructureRouters.genesStructure({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = GeneStructureFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for record: ${parsed.error.toString()}`)
      }
    }
  })

  it('returns schema-valid records for a direct transcript_id lookup', async () => {
    const input = { transcript_id: 'ENST00000456328', organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await genesStructureRouters.genesStructure({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = GeneStructureFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for record: ${parsed.error.toString()}`)
      }
    }
  })

  it('returns schema-valid records for a second, distinct gene_id', async () => {
    const input = { gene_id: geneAlt.gene_id, organism: 'Homo sapiens', page: 0, limit: 10 }
    const result: any = await genesStructureRouters.genesStructure({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = GeneStructureFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for record: ${parsed.error.toString()}`)
      }
    }
  })
})
