import { variantsProteinsRouters, outputFormat } from '../../../datatypeRouters/edges/variants_proteins'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// variants_proteins is fed by 4 structurally different sources (ADASTRA, UKB, IGVF, GVATdb),
// each merging distinct source-specific fields onto a shared base shape (see buildQuery's
// per-source MERGE branch in the router) - loop over all of them so a source-specific
// regression can't hide behind another source's passing rows. Both procedures resolve their
// side (protein or variant) with a direct point lookup before the single filtered edge scan.
describe('variantsProteinsRouters (integration)', () => {
  const cases: Array<{ source: string, variant_id: string, protein_id: string }> = [
    { source: 'ADASTRA', variant_id: 'NC_000019.10:2270368:C:T', protein_id: 'ENSP00000362300' },
    { source: 'UKB', variant_id: 'NC_000009.12:133263362:CGCCCACCACTACGCC:CGCC', protein_id: 'ENSP00000367026' },
    { source: 'IGVF', variant_id: 'NC_000010.11:44215:G:T', protein_id: 'ENSP00000377782' },
    { source: 'GVATdb', variant_id: 'NC_000004.12:1678376:C:T', protein_id: 'ENSP00000497310' }
  ]

  it.each(cases)('proteinsFromVariants returns schema-valid $source edges for a real variant', async (testCase) => {
    const input = { variant_id: testCase.variant_id, source: testCase.source, organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await variantsProteinsRouters.proteinsFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = outputFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.source} proteinsFromVariants record: ${parsed.error.toString()}`)
      }
    }
  })

  it.each(cases)('variantsFromProteins returns schema-valid $source edges for a real protein', async (testCase) => {
    const input = { protein_id: testCase.protein_id, source: testCase.source, organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await variantsProteinsRouters.variantsFromProteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = outputFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.source} variantsFromProteins record: ${parsed.error.toString()}`)
      }
    }
  })
})

// `method` (record.method) is a separate, more granular field from `source` on this
// collection - the cases above only ever filtered by `source`, so the `method` enum itself
// (ADASTRA, GVATdb, SEMVAR, pQTL) was never actually used as a filter. Cover it directly here.
describe('variantsProteinsRouters filtered by method (integration)', () => {
  const methodCases: Array<{ method: string, variant_id: string, protein_id: string }> = [
    { method: 'ADASTRA', variant_id: 'NC_000019.10:2270368:C:T', protein_id: 'ENSP00000362300' },
    { method: 'GVATdb', variant_id: 'NC_000004.12:1678376:C:T', protein_id: 'ENSP00000497310' },
    { method: 'SEMVAR', variant_id: 'NC_000010.11:44215:G:T', protein_id: 'ENSP00000377782' },
    { method: 'pQTL', variant_id: 'NC_000009.12:133263362:CGCCCACCACTACGCC:CGCC', protein_id: 'ENSP00000367026' }
  ]

  it.each(methodCases)('proteinsFromVariants returns schema-valid $method edges for a real variant', async (testCase) => {
    const input = { variant_id: testCase.variant_id, method: testCase.method, organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await variantsProteinsRouters.proteinsFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = outputFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.method} proteinsFromVariants record: ${parsed.error.toString()}`)
      }
    }
  })

  it.each(methodCases)('variantsFromProteins returns schema-valid $method edges for a real protein', async (testCase) => {
    const input = { protein_id: testCase.protein_id, method: testCase.method, organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await variantsProteinsRouters.variantsFromProteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = outputFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.method} variantsFromProteins record: ${parsed.error.toString()}`)
      }
    }
  })
})
