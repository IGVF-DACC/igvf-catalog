import { variantsPhenotypesRouters, variantPhenotypeFormat } from '../../../datatypeRouters/edges/variants_phenotypes'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// variants_phenotypes is fed by 4 structurally different methods (GWAS/SGE/cV2F/CRISPR
// screen), each returning a differently-shaped record - loop over all of them so a
// format-specific regression can't hide behind another method's passing rows.
//
// Known issue (tracked separately, not fixed here): GWAS edges can reference a variant that
// was never loaded into the variants collection. With verbose=true this DOCUMENT() lookup
// returns null, which fails output validation. This test samples a small page (limit=10) of
// GWAS edges, so it only catches this if one of the ~371 known-broken rows
// (data/scripts/broken_gwas_variant_ids.txt) happens to land in that page's sort order - it
// is not a reliable detector for this specific issue. Use the diagnostic AQL query (count of
// dangling edges per method) to actually track that; this test is here for schema drift on
// whatever real data it does see.
describe('variantsPhenotypesRouters.phenotypesFromVariants (integration)', () => {
  const methods = ['CRISPR screen', 'GWAS', 'SGE', 'cV2F']

  it.each(methods)('returns schema-valid %s edges for real data (verbose=false)', async (method) => {
    const input = { method, organism: 'Homo sapiens', verbose: 'false', page: 0, limit: 10 }
    const result: any = await variantsPhenotypesRouters.phenotypesFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = variantPhenotypeFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${method} record: ${parsed.error.toString()}`)
      }
    }
  })

  it.each(methods)('returns schema-valid %s edges for real data (verbose=true)', async (method) => {
    const input = { method, organism: 'Homo sapiens', verbose: 'true', page: 0, limit: 10 }
    const result: any = await variantsPhenotypesRouters.phenotypesFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = variantPhenotypeFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${method} record (verbose): ${parsed.error.toString()}`)
      }
    }
  })
})
