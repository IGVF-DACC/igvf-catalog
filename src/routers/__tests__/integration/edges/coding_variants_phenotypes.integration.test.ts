import {
  codingVariantsPhenotypesRouters,
  outputFormat,
  codingVariantsPhenotypeAggregationFormat,
  scoreSummaryOutputFormat
} from '../../../datatypeRouters/edges/coding_variants_phenotypes'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// coding_variants_phenotypes is fed by 6 structurally different scoring methods (MutPred2,
// ESM-1v, SGE, VAMP-seq, DUAL-IPA, Variant painting via fluorescence), each of which writes
// its score onto a different edge field (pathogenicity_score, esm_1v_score, score,
// dualipa_abun_score, localization_score) that the resolver folds into a single `score`
// output field - loop over all of them so a format-specific regression can't hide behind
// another method's passing rows.
describe('codingVariantsPhenotypesRouters.phenotypesFromCodingVariants (integration)', () => {
  const methods = ['DUAL-IPA', 'ESM-1v', 'MutPred2', 'SGE', 'VAMP-seq', 'Variant painting via fluorescence']

  it.each(methods)('returns schema-valid %s edges for real data', async (method) => {
    const input = { method, page: 0, limit: 5 }
    const result: any = await codingVariantsPhenotypesRouters.phenotypesFromCodingVariants({
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
        throw new Error(`Output validation failed for ${method} record: ${parsed.error.toString()}`)
      }
    }
  })
})

describe('codingVariantsPhenotypesRouters.codingVariantsFromPhenotypes (integration)', () => {
  // one real (phenotype_id, method) pair per scoring method, so each method's distinct score
  // field is exercised through the phenotype -> coding-variant direction too.
  const cases: Array<{ phenotype_id: string, method: string }> = [
    { phenotype_id: 'GO_0003674', method: 'MutPred2' },
    { phenotype_id: 'GO_0003674', method: 'ESM-1v' },
    { phenotype_id: 'NCIT_C16407', method: 'SGE' },
    { phenotype_id: 'OBA_0000128', method: 'VAMP-seq' },
    { phenotype_id: 'BAO_0040014', method: 'DUAL-IPA' },
    { phenotype_id: 'GO_0008104', method: 'Variant painting via fluorescence' }
  ]

  it.each(cases)('returns schema-valid $method edges for phenotype $phenotype_id', async (testCase) => {
    const input = { phenotype_id: testCase.phenotype_id, method: testCase.method, page: 0, limit: 5 }
    const result: any = await codingVariantsPhenotypesRouters.codingVariantsFromPhenotypes({
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
        throw new Error(`Output validation failed for ${testCase.method} record: ${parsed.error.toString()}`)
      }
    }
  })
})

describe('codingVariantsPhenotypesRouters.codingVariantsCountFromGene (integration)', () => {
  it('returns schema-valid counts for a real gene (cached path)', async () => {
    const input = { gene_id: 'ENSG00000000003' }
    const result: any = await codingVariantsPhenotypesRouters.codingVariantsCountFromGene({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = codingVariantsPhenotypeAggregationFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for count record: ${parsed.error.toString()}`)
      }
    }
  })
})

describe('codingVariantsPhenotypesRouters.codingVariantsSummary (integration)', () => {
  it('returns schema-valid score summaries for a real variant_id', async () => {
    const input = { variant_id: 'NC_000019.10:58352542:GC:CG' }
    const result: any = await codingVariantsPhenotypesRouters.codingVariantsSummary({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = scoreSummaryOutputFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for score summary record: ${parsed.error.toString()}`)
      }
    }
  })
})

// deprecatedCodingVariantsSummary is a separately exported procedure but shares the exact
// same resolver (phenotypeScoresFromVariant) as codingVariantsSummary above - still tested
// directly since it's its own exported procedure in codingVariantsPhenotypesRouters.
describe('codingVariantsPhenotypesRouters.deprecatedCodingVariantsSummary (integration)', () => {
  it('returns schema-valid score summaries for a real variant_id', async () => {
    const input = { variant_id: 'NC_000019.10:58352542:GC:CG' }
    const result: any = await codingVariantsPhenotypesRouters.deprecatedCodingVariantsSummary({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = scoreSummaryOutputFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for score summary record: ${parsed.error.toString()}`)
      }
    }
  })
})
