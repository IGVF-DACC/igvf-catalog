import { filesFilesetsRouters, filesFilesetsFormat } from '../../../datatypeRouters/nodes/files_filesets'
import { getCollectionEnumValuesOrThrow } from '../../../datatypeRouters/schema'

// Hits the real shared dev ArangoDB (config/development.json) - no jest.mock here on purpose.
// filesFilesets has a single exported procedure. Unlike complexes/drugs/genes, it has no
// TOKENS()/SEARCH-view fallback anywhere - every supported filter (including `method` and
// `source`) compiles into one equality FILTER clause on the `files_filesets` collection, so
// looping every real `method`/`source` enum value below is still just one cheap, bounded
// point-style query per case (LIMIT 5).
describe('filesFilesetsRouters.filesFilesets (integration)', () => {
  it('returns schema-valid records for a real file_fileset_id', async () => {
    const input = { file_fileset_id: 'ENCFF022FVI', limit: 5 }
    const result: any = await filesFilesetsRouters.filesFilesets({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = filesFilesetsFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })

  // Confirmed against the live dev DB (see probe script used while authoring this test) that
  // every one of these real enum values has at least one matching document, except
  // 'scATAC-seq' - no files_filesets record currently carries that exact method value (the
  // closest real data is 'snATAC-seq'), so it's excluded here rather than asserting a
  // guaranteed-empty result.
  const methods = getCollectionEnumValuesOrThrow('nodes', 'files_filesets', 'method')
    .filter((method) => method !== 'scATAC-seq')

  it.each(methods.map((method) => ({ method })))('returns schema-valid records for method=$method', async (testCase) => {
    const input = { method: testCase.method, limit: 5 }
    const result: any = await filesFilesetsRouters.filesFilesets({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = filesFilesetsFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for method=${testCase.method} record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })

  const sources = getCollectionEnumValuesOrThrow('nodes', 'files_filesets', 'source')

  it.each(sources.map((source) => ({ source })))('returns schema-valid records for source=$source', async (testCase) => {
    const input = { source: testCase.source, limit: 5 }
    const result: any = await filesFilesetsRouters.filesFilesets({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    for (const record of result) {
      const parsed = filesFilesetsFormat.safeParse(record)
      if (!parsed.success) {
        throw new Error(`Output validation failed for source=${testCase.source} record ${record._id as string}: ${parsed.error.toString()}`)
      }
    }
  })
})
