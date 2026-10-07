import { variantsGenomicElementsRouters, genomicElementsFromVariantsOutputFormat } from '../../../datatypeRouters/edges/variants_genomic_elements'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
//
// This router exports 6 procedures; only 2 have a genuinely cheap, single point-lookup path
// and are covered below. The other 4 are deliberately skipped because every input path they
// support forces an expensive query shape - not because we forgot a procedure:
//
// - genomicElementsFromVariantsCount: findInterceptingGenomicElementsPerID() always scans
//   genomic_elements for chr/start/end overlap with no index hint (the same interval-overlap
//   shape that variants_genomic_elements_genes.ts's code comment documents as ~10s without a
//   forced index hint, vs ~0.4s with one).
// - predictionsFromVariants: joins variants -> genomic_elements via the same un-hinted
//   chr/start <= pos/end >= pos overlap, then a third nested FOR into
//   genomic_elements_genes - a multi-stage per-row join, not a single point lookup.
// - genomicElementsPredictionsFromVariant: same un-hinted genomic_elements overlap scan,
//   with no LIMIT at all on the number of overlapping elements/genes considered.
// - variantsRegionSummary: for every variant in the (up to 10kb) region it fans out into 5
//   separate per-row sub-queries (variants_genes, variants_proteins, variants_biosamples,
//   variants_genomic_elements, variants_phenotypes) with no result LIMIT - an unbounded
//   per-row aggregation.
//
// The 2 covered procedures avoid all of that: genomicElementsFromVariants is queried by
// variant_id (a direct variantIDSearch point lookup) without biological_context, so only the
// single exact-match branch runs (no prefix/token/Levenshtein cascade against the search
// view). variantsFromGenomicElements is queried by method only (no region), so the
// genomic_elements region-overlap branch is skipped entirely and it's a single filtered scan
// of variants_genomic_elements with a small LIMIT.
describe('variantsGenomicElementsRouters (integration)', () => {
  it('genomicElementsFromVariants returns schema-valid edges for a real variant (exact match only, no biological_context)', async () => {
    const input = { variant_id: 'NC_000001.11:100000722:G:A', method: 'caQTL', page: 0, limit: 5 }
    const result: any = await variantsGenomicElementsRouters.genomicElementsFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = genomicElementsFromVariantsOutputFormat.element.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for genomicElementsFromVariants record: ${parsed.error.toString()}`)
      }
    }
  })

  it('variantsFromGenomicElements returns schema-valid edges for a real method (no region scan)', async () => {
    const input = { method: 'caQTL', page: 0, limit: 5 }
    const result: any = await variantsGenomicElementsRouters.variantsFromGenomicElements({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = genomicElementsFromVariantsOutputFormat.element.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for variantsFromGenomicElements record: ${parsed.error.toString()}`)
      }
    }
  })
})
