import { genesRouters, geneFormat } from '../../../datatypeRouters/nodes/genes'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// genes has a single exported procedure. gene_id/hgnc_id/entrez all resolve to a plain
// equality FILTER on an indexed field of the `genes` (or, for Mus musculus, `mm_genes`)
// collection - a real match on any of them short-circuits before the router ever falls back
// to its `name`/`synonym` TOKENS()/LEVENSHTEIN_MATCH text-search cascade, so that fallback
// is never triggered by these inputs. That cascade itself is intentionally not exercised
// here per the integration-tier performance constraint (only ID-style filters).
describe('genesRouters.genes (integration)', () => {
  const cases: Array<{ label: string, input: Record<string, string | number> }> = [
    { label: 'gene_id (human)', input: { gene_id: 'ENSG00000179967', limit: 5 } },
    { label: 'hgnc_id (human)', input: { hgnc_id: '16330', limit: 5 } },
    { label: 'entrez (human)', input: { entrez: '100507617', limit: 5 } },
    { label: 'gene_id (mouse)', input: { gene_id: 'ENSMUSG00000126297', organism: 'Mus musculus', limit: 5 } }
  ]

  it.each(cases)('returns schema-valid records filtered by $label', async (testCase) => {
    const result: any = await genesRouters.genes({
      input: testCase.input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: testCase.input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = geneFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.label} record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })
})
