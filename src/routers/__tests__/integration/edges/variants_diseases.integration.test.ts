import { variantsDiseasesRouters, variantDiseaseFormat } from '../../../datatypeRouters/edges/variants_diseases'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// Only the disease_id / variant_id point-lookup paths are exercised here. variantsFromDiseases
// also supports a disease_name path that falls back to a SEARCH TOKENS query against a text
// search view - that cascade is intentionally not exercised (see CRITICAL CONSTRAINT #1).
describe('variantsDiseasesRouters.diseaseFromVariants (integration)', () => {
  it('returns schema-valid disease edges for a real variant_id', async () => {
    const input = { variant_id: 'NC_000012.12:102917129:T:C', organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await variantsDiseasesRouters.diseaseFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = variantDiseaseFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for disease record: ${parsed.error.toString()}`)
      }
    }
  })
})

describe('variantsDiseasesRouters.variantsFromDiseases (integration)', () => {
  it('returns schema-valid variant edges for a real disease_id', async () => {
    const input = { disease_id: 'MONDO_0009861', organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await variantsDiseasesRouters.variantsFromDiseases({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = variantDiseaseFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for variant record: ${parsed.error.toString()}`)
      }
    }
  })
})
