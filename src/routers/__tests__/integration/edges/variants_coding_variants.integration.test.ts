import { variantsCodingVariantsRouters } from '../../../datatypeRouters/edges/variants_coding_variants'
import { codingVariantsFormat } from '../../../datatypeRouters/nodes/coding_variants'
import { variantSimplifiedFormat } from '../../../datatypeRouters/nodes/variants'
import { z } from 'zod'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
const variantsFromCodingVariantsFormat = variantSimplifiedFormat.merge(z.object({ _id: z.string() }))

describe('variantsCodingVariantsRouters.codingVariantsFromVariants (integration)', () => {
  it('returns schema-valid coding variants for a real variant_id', async () => {
    const input = { variant_id: 'NC_000010.11:47056:C:A', page: 0, limit: 5 }
    const result: any = await variantsCodingVariantsRouters.codingVariantsFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = codingVariantsFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for coding variant record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })
})

describe('variantsCodingVariantsRouters.variantsFromCodingVariants (integration)', () => {
  // Deliberately filtering by hgvsp here, not protein_id/gene_name/transcript_id: those filters
  // on the coding_variants collection turned out to be un-indexed full collection scans
  // (~5-8s for a LIMIT 5 query against real dev data - see final report), which would violate
  // the "fast point lookup" requirement for this test tier. hgvsp resolves in <1s.
  it('returns schema-valid variants for a real hgvsp', async () => {
    const input = { hgvsp: 'p.Ter445Tyrext*?', page: 0, limit: 5 }
    const result: any = await variantsCodingVariantsRouters.variantsFromCodingVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = variantsFromCodingVariantsFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for variant record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })
})
