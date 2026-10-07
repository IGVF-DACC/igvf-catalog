import { variantsBiosamplesRouters, returnFormat } from '../../../datatypeRouters/edges/variants_biosamples'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// variants_biosamples holds 3 structurally different methods (BlueSTARR, STARR-seq, MPRA) - the
// resolver branches its RETURN shape on record.method (e.g. genomic_element is only populated
// for BlueSTARR/MPRA, DNA/RNA counts only for STARR-seq/MPRA) - loop over all 3 so a
// method-specific regression can't hide behind another method's passing rows.
describe('variantsBiosamplesRouters.variantsFromBiosamples (integration)', () => {
  const cases: Array<{ method: string, biosample_id: string }> = [
    { method: 'BlueSTARR', biosample_id: 'EFO_0001086' },
    { method: 'STARR-seq', biosample_id: 'EFO_0002067' },
    { method: 'MPRA', biosample_id: 'CL_0000679' }
  ]

  it.each(cases)('returns schema-valid $method edges for a real biosample', async (testCase) => {
    const input = { biosample_id: testCase.biosample_id, method: testCase.method, organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await variantsBiosamplesRouters.variantsFromBiosamples({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = returnFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.method} record: ${parsed.error.toString()}`)
      }
      expect(record.method).toBe(testCase.method)
    }
  })
})

describe('variantsBiosamplesRouters.biosamplesFromVariants (integration)', () => {
  const cases: Array<{ method: string, variant_id: string }> = [
    { method: 'BlueSTARR', variant_id: 'NC_000001.11:100003003:A:G' },
    { method: 'STARR-seq', variant_id: '_4Zi6bh6LmDnMl82fKOKsx413kAx7UPD' },
    { method: 'MPRA', variant_id: 'NC_000020.11:63182006:GCCAGAAAGCAGGACCCTCCCTCACGGGCACCGCCAGAAAGCAGGACCCTCCCTCACGGGCACCGCCAGAAAGCAGGACCCTCCCTCAC:GCCAGAAAGCAGGACCCTCCCTCACGGGCACCGCCAGAAAGCAGGACCCTCCCTCAC' }
  ]

  it.each(cases)('returns schema-valid $method edges for a real variant', async (testCase) => {
    const input = { variant_id: testCase.variant_id, method: testCase.method, organism: 'Homo sapiens', page: 0, limit: 5 }
    const result: any = await variantsBiosamplesRouters.biosamplesFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = returnFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.method} record: ${parsed.error.toString()}`)
      }
      expect(record.method).toBe(testCase.method)
    }
  })
})
