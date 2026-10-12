import { diseasesGenesRouters, diseasesToGenesFormat } from '../../../datatypeRouters/edges/diseases_genes'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// diseases_genes merges 2 structurally different sources (Orphanet vs GenCC, e.g. sgc_id/hgnc/
// classification only ever appear on GenCC edges, association_type/association_status only on
// Orphanet edges) - test each source against real data so a schema drift specific to one
// source's shape can't hide behind the other's passing rows.
describe('diseasesGenesRouters.genesFromDiseases (integration)', () => {
  const cases: Array<{ source: string, disease_id: string }> = [
    { source: 'Orphanet', disease_id: 'Orphanet_166024' },
    { source: 'GenCC', disease_id: 'MONDO_0024535' }
  ]

  it.each(cases)('returns schema-valid $source genes for a real disease_id', async (testCase) => {
    const input = { disease_id: testCase.disease_id, source: testCase.source, organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await diseasesGenesRouters.genesFromDiseases({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = diseasesToGenesFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.source} record: ${parsed.error.toString()}`)
      }
    }
  })

  // verbose=true swaps the bare `disease`/`gene` _id references for fully resolved node
  // objects via a separate DOCUMENT()-backed subquery - a distinct code path worth covering.
  it('returns schema-valid genes for a real disease_id (verbose=true)', async () => {
    const input = { disease_id: 'Orphanet_166024', organism: 'Homo sapiens', verbose: 'true', page: 0, limit: 5 }
    const result: any = await diseasesGenesRouters.genesFromDiseases({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = diseasesToGenesFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for verbose record: ${parsed.error.toString()}`)
      }
    }
  })
})

describe('diseasesGenesRouters.diseasesFromGenes (integration)', () => {
  const verboseCases = ['false', 'true']

  it.each(verboseCases)('returns schema-valid diseases for a real gene_id (verbose=%s)', async (verbose) => {
    const input = { gene_id: 'ENSG00000115267', organism: 'Homo sapiens', verbose, page: 0, limit: 5 }
    const result: any = await diseasesGenesRouters.diseasesFromGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = diseasesToGenesFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for record (verbose=${verbose}): ${parsed.error.toString()}`)
      }
    }
  })
})
