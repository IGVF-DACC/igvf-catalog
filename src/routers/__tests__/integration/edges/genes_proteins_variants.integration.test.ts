import { genesProteinsVariants, sequenceVariantRelatedFormat } from '../../../datatypeRouters/edges/genes_proteins_variants'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
//
// Only genesProteinsFromVariants is covered here. The other two procedures in this router
// (variantsFromGeneProteins, genesProteinsGenesProteins) are driven by a free-text `query`
// param resolved via geneIds()/proteinIds() (an OR-scan across several non-indexed fields),
// and their underlying AQL aggregates an entire edge collection's worth of rows (COLLECT with
// no LIMIT inside the LET block, only applied after the full aggregation) or does per-row
// nested sub-queries (genesProteinsFromGenes/genesProteinsFromProteins fan out a nested FOR
// per transcript/protein with no bound on the intermediate set). Both are unbounded/expensive
// paths per the fast-integration-test constraint, so they are intentionally skipped here.
describe('genesProteinsVariants.genesProteinsFromVariants (integration)', () => {
  it('returns schema-valid gene/protein relations for a real variant', async () => {
    const input = { variant_id: 'NC_000010.11:79347741:AGGT:TCAG', page: 0, limit: 10 }
    const result: any = await genesProteinsVariants.genesProteinsFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = sequenceVariantRelatedFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for genesProteinsFromVariants record: ${parsed.error.toString()}`)
      }
    }
  })
})
