import { variantsRouters, variantFormat, variantsAllelesFormat } from '../../../datatypeRouters/nodes/variants'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
//
// `variants` (1.87 BILLION documents on db-dev) is by far the largest collection touched by
// this integration tier, so every query shape used below was verified with db.explain() against
// the live DB to confirm it compiles to an IndexNode (never an EnumerateCollectionNode) before
// being included here:
//   - `record._key == X`                                      -> primary index
//   - `'X' IN record.rsid`                                    -> idx_persistent_rsid[*]
//   - `'X' IN record.rsid AND record.annotations.<f> range`   -> idx_persistent_rsid[*] (range
//                                                                 filtered post-index, still cheap
//                                                                 since rsid narrows to ~1 doc)
//   - forced `idx_zkd_pos` region scan, capped at a 300bp span -> zkd index, explicit forceIndexHint
//
// `variantSummary` (variantsRouters.variantSummary) is intentionally NOT covered here: even
// though its own input is a simple point identifier (spdi/hgvs/ca_id/variant_id), its resolver
// internally fans out into several more DB round trips per call - two nearestGeneSearch() calls
// (each itself a 2-stage "in-region, else nearest-neighbor L/R" query against `genes`) plus a
// 7-collection edge-aggregation query (variants_genes, variants_drugs, variants_proteins,
// variants_diseases, variants_phenotypes, variants_biosamples, variants_genomic_elements). That
// chain of several sequential/aggregated queries per single request doesn't match the "single
// indexed point lookup with a small limit" bar for this tier, so it's skipped here.
describe('variantsRouters.variants (integration)', () => {
  const cases: Array<{ label: string, input: Record<string, string | number> }> = [
    { label: 'variant_id (human)', input: { variant_id: 'NC_000019.10:44908821:C:T', limit: 5 } },
    { label: 'variant_id (mouse)', input: { variant_id: 'NC_000067.7:3050706:GGGGGGGGG:GGGGGGGGGG', organism: 'Mus musculus', limit: 5 } }
  ]

  it.each(cases)('returns schema-valid records filtered by $label', async (testCase) => {
    const result: any = await variantsRouters.variants({
      input: testCase.input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: testCase.input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = variantFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for ${testCase.label} record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })
})

describe('variantsRouters.variantByFrequencySource (integration)', () => {
  // rs7412 (APOE, variants/NC_000019.10:44908821:C:T) has every gnomad_af_*/bravo_af annotation
  // populated on db-dev, so it's used as the single fixed point lookup (via `rsid`, indexed) for
  // every `source` enum value - each iteration is still one indexed lookup, just varying which
  // annotation field the range filter is applied to.
  const sources = [
    'bravo_af',
    'gnomad_af_total',
    'gnomad_af_afr',
    'gnomad_af_afr_female',
    'gnomad_af_afr_male',
    'gnomad_af_ami',
    'gnomad_af_ami_female',
    'gnomad_af_ami_male',
    'gnomad_af_amr',
    'gnomad_af_amr_female',
    'gnomad_af_amr_male',
    'gnomad_af_asj',
    'gnomad_af_asj_female',
    'gnomad_af_asj_male',
    'gnomad_af_eas',
    'gnomad_af_eas_female',
    'gnomad_af_eas_male',
    'gnomad_af_female',
    'gnomad_af_fin',
    'gnomad_af_fin_female',
    'gnomad_af_fin_male',
    'gnomad_af_male',
    'gnomad_af_nfe',
    'gnomad_af_nfe_female',
    'gnomad_af_nfe_male',
    'gnomad_af_oth',
    'gnomad_af_oth_female',
    'gnomad_af_oth_male',
    'gnomad_af_sas',
    'gnomad_af_sas_male',
    'gnomad_af_sas_female',
    'gnomad_af_raw'
  ]

  const cases: Array<{ source: string }> = sources.map((source) => ({ source }))

  it.each(cases)('returns schema-valid records for source=$source', async (testCase) => {
    const input = { source: testCase.source, rsid: 'rs7412', limit: 5 }
    const result: any = await variantsRouters.variantByFrequencySource({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = variantFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for source=${testCase.source} record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })
})

describe('variantsRouters.variantsAlleles (integration)', () => {
  // Bounded to a 300bp span (the resolver rejects anything over 1kb) around the APOE locus,
  // which is known to contain variants on db-dev; the query itself forces idx_zkd_pos via
  // forceIndexHint, confirmed index-backed (not a full scan) via db.explain().
  it('returns a schema-valid allele matrix for a small real region', async () => {
    const input = { region: 'chr19:44908600-44908900' }
    const result: any = await variantsRouters.variantsAlleles({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(1)

    const parsed = variantsAllelesFormat.safeParse(result)
    if (!parsed.success) {
      throw new Error(`Output validation failed for variantsAlleles region result: ${parsed.error.toString()}`)
    }
  })
})
