import { variantsDrugsRouters, variantsToDrugsFormat, drugsToVariantsFormat } from '../../../datatypeRouters/edges/variants_drugs'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// variants_drugs exposes two procedures, one per traversal direction. Both resolvers do a
// single indexed point lookup (drug _id or variant _id) followed by one filtered edge scan
// with a small LIMIT - no free-text cascades or region scans are involved.
//
// Both output formats are declared as `z.object({...}).transform(...)` (they rename the raw
// `_from`/`_to` edge fields into `sequence_variant`/`drug`). Calling the procedure the way the
// pilot files do runs tRPC's actual input/output pipeline, so by the time `result` reaches
// this test the transform has already run and `_from`/`_to` are gone from the record - re-
// parsing that already-transformed record against the *same* schema (which still requires the
// pre-transform `_from`/`_to` keys) would always fail even on perfectly valid data. Instead we
// derive the real post-transform shape from the same exported schema via
// `.innerType().omit(...)` (the transform only drops `_from`/`_to`; it doesn't add any field
// the schema doesn't already declare), so we're still validating against the router's real
// output schema, just accounting for the transform step it defines.
const drugsToVariantsPostTransformFormat = drugsToVariantsFormat.innerType().omit({ _to: true })
const variantsToDrugsPostTransformFormat = variantsToDrugsFormat.innerType().omit({ _from: true })
describe('variantsDrugsRouters (integration)', () => {
  it('variantsFromDrugs returns schema-valid variants for a real drug', async () => {
    const input = { drug_id: 'PA450085', organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await variantsDrugsRouters.variantsFromDrugs({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = drugsToVariantsPostTransformFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for variantsFromDrugs record: ${parsed.error.toString()}`)
      }
    }
  })

  it('drugsFromVariants returns schema-valid drugs for a real variant', async () => {
    const input = { variant_id: 'NC_000019.10:41354390:A:G', organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await variantsDrugsRouters.drugsFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = variantsToDrugsPostTransformFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for drugsFromVariants record: ${parsed.error.toString()}`)
      }
    }
  })
})
