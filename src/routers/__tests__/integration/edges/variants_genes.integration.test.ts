import { variantsGenesRouters, completeQtlsFormat, qtlsSummaryFormat } from '../../../datatypeRouters/edges/variants_genes'
import { geneFormat } from '../../../datatypeRouters/nodes/genes'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
describe('variantsGenesRouters.nearestGenes (integration)', () => {
  it('returns schema-valid coding-region genes for a real region', async () => {
    const input = { region: 'chr1:33306765-33321098' }
    const result: any = await variantsGenesRouters.nearestGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = geneFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for gene record: ${parsed.error.toString()}`)
      }
    }
  })
})

// variants_genes holds AFGR sQTL/eQTL, EBI eQTL Catalog, and CRISPR variant-gene edges under
// 4 distinct `method` values - loop over all of them so a format-specific regression can't
// hide behind another method's passing rows. Deliberately omitting biological_context, which
// triggers an exact->prefix->token->Levenshtein fallback cascade (expensive, out of scope for
// this test tier) - without it, both resolvers run exactly one exact-match query.
describe('variantsGenesRouters.variantsFromGenes (integration)', () => {
  const cases: Array<{ method: string, gene_id: string }> = [
    { method: 'CRISPR screen', gene_id: 'ENSG00000177455' },
    { method: 'Variant-EFFECTS', gene_id: 'ENSG00000134460' },
    { method: 'eQTL', gene_id: 'ENSG00000182534' },
    { method: 'spliceQTL', gene_id: 'ENSG00000163913' }
  ]

  it.each(cases)('returns schema-valid $method edges for a real gene', async (testCase) => {
    const input = { gene_id: testCase.gene_id, method: testCase.method, organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await variantsGenesRouters.variantsFromGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = completeQtlsFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.method} record: ${parsed.error.toString()}`)
      }
    }
  })
})

describe('variantsGenesRouters.genesFromVariants (integration)', () => {
  const cases: Array<{ method: string, variant_id: string }> = [
    { method: 'CRISPR screen', variant_id: 'NC_000016.10:28930707:T:C' },
    { method: 'Variant-EFFECTS', variant_id: 'NC_000010.11:6062514:AGGAT:CAGTC' },
    { method: 'eQTL', variant_id: 'NC_000017.11:76710350:G:A' },
    { method: 'spliceQTL', variant_id: 'NC_000003.12:129450782:C:T' }
  ]

  it.each(cases)('returns schema-valid $method edges for a real variant', async (testCase) => {
    const input = { variant_id: testCase.variant_id, method: testCase.method, organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await variantsGenesRouters.genesFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = completeQtlsFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.method} record: ${parsed.error.toString()}`)
      }
    }
  })
})

describe('variantsGenesRouters.qtlSummaryEndpoint (integration)', () => {
  it('returns a schema-valid summary for a real variant', async () => {
    const input = { variant_id: 'NC_000017.11:76710350:G:A', page: 0 }
    const result: any = await variantsGenesRouters.qtlSummaryEndpoint({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = qtlsSummaryFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for qtl summary record: ${parsed.error.toString()}`)
      }
    }
  })
})
