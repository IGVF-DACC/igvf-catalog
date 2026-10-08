import { variantsVariantsRouters, variantsVariantsFormat } from '../../../datatypeRouters/edges/variants_variants'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
//
// This router exports 2 procedures. Only variantsFromVariantID is covered here.
// variantsFromVariantIDSummary (findVariantLDSummary) is deliberately skipped: for every
// matched LD row (before its LIMIT is applied - the LET clauses sit between FILTER/SORT and
// LIMIT in the query text) it runs two more nested aggregation sub-queries against
// variants_genes and variants_proteins (COLLECT ... INTO group, per-group sub-aggregations).
// That's a per-row sub-query fan-out, not a single bounded point lookup, and the router source
// itself has a comment acknowledging a known performance issue here ("temporarily removing
// genomic elements related queries until we have a better way to handle the performance").
//
// variantsFromVariantID (findVariantLDs) is safe: it resolves the variant with a direct
// variantIDSearch point lookup, then the LD edge scan applies LIMIT before the per-row verbose
// lookup / addVariantData batch lookup run - both bounded by the already-limited result set.
describe('variantsVariantsRouters.variantsFromVariantID (integration)', () => {
  it('returns schema-valid LD edges for a real variant', async () => {
    const input = { variant_id: 'NC_000001.11:10929:G:A', organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await variantsVariantsRouters.variantsFromVariantID({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = variantsVariantsFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for variantsFromVariantID record: ${parsed.error.toString()}`)
      }
    }
  })
})
