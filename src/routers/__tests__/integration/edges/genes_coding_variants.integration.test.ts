import {
  genesCodingVariantsRouters,
  codingVariantsScoresFormat,
  allCodingVariantsScoresFormat
} from '../../../datatypeRouters/edges/genes_coding_variants'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// codingVariantsFromGenes reads from a precomputed per-gene cache (genes_coding_variants_scores,
// point lookup by _key = gene_id). The optional `method` param filters *inside* that cached
// document rather than issuing a different query shape, but it is still a separate code path
// (cachedFindCodingVariantsFromGenes's method-provided branch) worth covering directly.
//
// Known issue (not fixed here): the outer resolver deletes `input.limit` before calling
// cachedFindCodingVariantsFromGenes, so a caller-supplied `limit` is silently ignored on this
// cached path (it always falls back to the hardcoded default of 25) - the requested limit=5
// below has no effect on the cached branch's result size.
describe('genesCodingVariantsRouters.codingVariantsFromGenes (integration)', () => {
  const cases: Array<{ method?: string, gene_id: string }> = [
    { gene_id: 'ENSG00000137463' },
    { gene_id: 'ENSG00000137463', method: 'ESM-1v' }
  ]

  it.each(cases)('returns schema-valid coding-variant scores for a real gene ($method)', async (testCase) => {
    const input: Record<string, unknown> = { gene_id: testCase.gene_id, organism: 'Homo sapiens', page: 0, limit: 5 }
    if (testCase.method !== undefined) {
      input.method = testCase.method
    }
    const result: any = await genesCodingVariantsRouters.codingVariantsFromGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = codingVariantsScoresFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for record: ${parsed.error.toString()}`)
      }
    }
  })
})

describe('genesCodingVariantsRouters.allCodingVariantsFromGenes (integration)', () => {
  const cases: Array<{ dataset: string, gene_id: string }> = [
    { dataset: 'MutPred2', gene_id: 'ENSG00000137463' },
    { dataset: 'ESM-1v', gene_id: 'ENSG00000137463' }
  ]

  it.each(cases)('returns schema-valid $dataset scores for a real gene', async (testCase) => {
    const input = { gene_id: testCase.gene_id, dataset: testCase.dataset, page: 0, limit: 5 }
    const result: any = await genesCodingVariantsRouters.allCodingVariantsFromGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    const parsed = allCodingVariantsScoresFormat.safeParse(result)
    if (!parsed.success) {
      throw new Error(`Output validation failed for ${testCase.dataset} result: ${parsed.error.toString()}`)
    }
  })
})
