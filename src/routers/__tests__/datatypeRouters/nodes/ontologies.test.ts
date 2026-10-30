import { ontologyRouters } from '../../../datatypeRouters/nodes/ontologies'
import * as dbModule from '../../../../database'
import * as helpers from '../../../datatypeRouters/_helpers'

jest.mock('../../../../database')
// probeThenFetchPage must keep its real implementation (it's what the limit/pagination fix
// relies on) - only getFilterStatements/getDBReturnStatements are stubbed per test.
jest.mock('../../../datatypeRouters/_helpers', () => ({
  ...jest.requireActual('../../../datatypeRouters/_helpers'),
  getFilterStatements: jest.fn(),
  getDBReturnStatements: jest.fn()
}))

// db.query is called twice per stage now (a cheap LIMIT 1 existence probe, then the real
// page fetch) - keying the mock by query text (which stage it belongs to) rather than call
// order/count means both calls for the stage that "wins" naturally return the same data,
// matching real behavior, without hand-sequencing mockResolvedValueOnce per call.
function mockDbQueryByStage (stageResults: { exact?: any[], prefix?: any[], token?: any[], fuzzy?: any[] }): void {
  jest.spyOn(dbModule.db, 'query').mockImplementation(async (query: unknown) => {
    const text = String(query)
    let result: any[] = []
    if (text.includes('LEVENSHTEIN_MATCH')) {
      result = stageResults.fuzzy ?? []
    } else if (text.includes('TOKENS(') && text.includes('SEARCH')) {
      result = stageResults.token ?? []
    } else if (text.includes('STARTS_WITH')) {
      result = stageResults.prefix ?? []
    } else {
      result = stageResults.exact ?? []
    }
    return { all: async () => result } as any
  })
}

describe('ontologyRouters.ontologyTerm', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns ontology terms by exact match', async () => {
    const mockResult = [{
      uri: 'uri1',
      term_id: 'T1',
      name: 'Gene Ontology',
      synonyms: ['GO'],
      description: 'desc',
      source: 'GO',
      subontology: 'biological_process',
      source_url: 'url'
    }]
    mockDbQueryByStage({ exact: mockResult })
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('term_id == "T1"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('uri, term_id, name, synonyms, description, source, subontology, source_url')

    const input = { term_id: 'T1', page: 0 }
    const result = await ontologyRouters.ontologyTerm({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('returns fuzzy results if no exact, prefix, or token match and name is provided', async () => {
    const fuzzyResult = [{ uri: 'uri2', term_id: 'T2', name: 'Fuzzy Term' }]
    mockDbQueryByStage({ fuzzy: fuzzyResult })
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('uri, term_id, name')

    const input = { name: 'Fuzzy Term', page: 0 }
    const result = await ontologyRouters.ontologyTerm({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(fuzzyResult)
  })

  it('does not overlap or skip rows across pages when a stage is exhausted mid-cascade', async () => {
    // 27 prefix matches total - page 0 gets the first 25, page 1 gets the remaining 2. Page 1
    // must NOT fall through to token/fuzzy just because 2 < limit.
    const allPrefixMatches = Array.from({ length: 27 }, (_, i) => ({ uri: `uri${i}`, term_id: `T${i}`, name: `lupus ${i}` }))
    jest.spyOn(dbModule.db, 'query').mockImplementation(async (query: unknown) => {
      const text = String(query)
      if (text.includes('STARTS_WITH')) {
        const offsetLimitMatch = /LIMIT (\d+), (\d+)/.exec(text)
        let offset = 0
        let limit = allPrefixMatches.length
        if (offsetLimitMatch) {
          offset = Number(offsetLimitMatch[1])
          limit = Number(offsetLimitMatch[2])
        } else {
          const plainLimitMatch = /LIMIT (\d+)\b/.exec(text)
          if (plainLimitMatch) {
            limit = Number(plainLimitMatch[1])
          }
        }
        return { all: async () => allPrefixMatches.slice(offset, offset + limit) } as any
      }
      // exact match stage always empty for this name
      return { all: async () => [] } as any
    })
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('uri, term_id, name')

    const page0Input = { name: 'lupus', page: 0, limit: 25 }
    const page0 = await ontologyRouters.ontologyTerm({ input: page0Input, ctx: {}, type: 'query', path: '', rawInput: page0Input }) as any[]
    const page1Input = { name: 'lupus', page: 1, limit: 25 }
    const page1 = await ontologyRouters.ontologyTerm({ input: page1Input, ctx: {}, type: 'query', path: '', rawInput: page1Input }) as any[]
    const page2Input = { name: 'lupus', page: 2, limit: 25 }
    const page2 = await ontologyRouters.ontologyTerm({ input: page2Input, ctx: {}, type: 'query', path: '', rawInput: page2Input }) as any[]

    expect(page0).toHaveLength(25)
    expect(page1).toHaveLength(2)
    expect(page2).toHaveLength(0)
    const ids = [...page0, ...page1].map((r: any) => r.term_id)
    expect(new Set(ids).size).toBe(27) // no duplicates/overlap across pages
  })

  it('caps limit to MAX_PAGE_SIZE', async () => {
    mockDbQueryByStage({})
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('uri, term_id')

    const input = { page: 0, limit: 5000 }
    await ontologyRouters.ontologyTerm({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('returns empty array if no results found', async () => {
    mockDbQueryByStage({})
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('uri, term_id')

    const input = { page: 0 }
    const result = await ontologyRouters.ontologyTerm({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual([])
  })

  it('sorts prefix and token/fuzzy search stages with a deterministic tiebreaker', async () => {
    // Regression guard for NCIT_C60959 appearing on both page 0 and page 1 of
    // ?name=cancer lung: probeThenFetchPage runs a separate query execution per page, so a
    // stage with no (or no fully deterministic) SORT can place a tied/unordered row in the
    // overlapping edge of two different pages. A mocked DB can't catch this itself (it slices
    // deterministically regardless of the real SORT clause), so assert directly on the AQL.
    const queries: string[] = []
    jest.spyOn(dbModule.db, 'query').mockImplementation(async (query: unknown) => {
      queries.push(String(query))
      return { all: async () => [] } as any
    })
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('uri, term_id, name')

    const input = { name: 'cancer lung', page: 0, limit: 25 }
    await ontologyRouters.ontologyTerm({ input, ctx: {}, type: 'query', path: '', rawInput: input })

    const prefixQuery = queries.find(q => q.includes('STARTS_WITH'))
    expect(prefixQuery).toContain('SORT record._key')

    const tokenQuery = queries.find(q => q.includes('TOKENS(') && q.includes('SEARCH'))
    expect(tokenQuery).toContain('SORT BM25(record) DESC, record._key')
  })

  it('transforms files_fileset input into a files_filesets filter', async () => {
    mockDbQueryByStage({})
    const getFilterStatementsSpy = jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('uri, term_id')

    const input = { files_fileset: 'IGVFFI7407XTPX', page: 0 }
    await ontologyRouters.ontologyTerm({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    const passedInput = getFilterStatementsSpy.mock.calls[0][1]
    expect(passedInput.files_filesets).toBe('files_filesets/IGVFFI7407XTPX')
    expect(passedInput.files_fileset).toBeUndefined()
  })
})
