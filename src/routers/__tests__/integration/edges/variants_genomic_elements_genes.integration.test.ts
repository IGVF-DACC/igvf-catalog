import { variantsGenomicElementsGenesRouters, outputFormat } from '../../../datatypeRouters/edges/variants_genomic_elements_genes'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
//
// This router exports a single procedure (variantsGenomicElementsGenes). Its resolver is the
// "fast" version of the genomic-elements-overlap pattern: it resolves the variant with a
// direct point lookup, then intersects it with genomic_elements using an explicit
// `OPTIONS { indexHint: "idx_persistent_chr_start_end", forceIndexHint: true }` (the code
// comment documents this as ~0.4s vs ~10s without the hint), filtering by method in
// application code afterward. The final join against genomic_elements_genes only iterates the
// small in-memory `@elements` array already resolved above, not a fresh collection scan, and
// is bounded by a small LIMIT. No procedures in this file are skipped.
describe('variantsGenomicElementsGenesRouters.variantsGenomicElementsGenes (integration)', () => {
  const cases: Array<{ nearbyGenes: 'true' | 'false' }> = [
    { nearbyGenes: 'true' },
    { nearbyGenes: 'false' }
  ]

  it.each(cases)('returns schema-valid gene records for a real variant (nearby_genes=$nearbyGenes)', async (testCase) => {
    const input = { variant_id: 'NC_000001.11:1000023:C:T', nearby_genes: testCase.nearbyGenes, page: 0, limit: 5 }
    const result: any = await variantsGenomicElementsGenesRouters.variantsGenomicElementsGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = outputFormat.element.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for nearby_genes=${testCase.nearbyGenes} record: ${parsed.error.toString()}`)
      }
    }
  })
})
