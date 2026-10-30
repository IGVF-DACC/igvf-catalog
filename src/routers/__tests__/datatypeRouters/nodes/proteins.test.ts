import { proteinsRouters } from '../../../datatypeRouters/nodes/proteins'
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

// Proper AQL format for getDBReturnStatements mock
const mockDBReturnStatements = '_id: record._key, \'name\': record[\'name\'], \'uniprot_names\': record[\'uniprot_names\'], \'uniprot_full_names\': record[\'uniprot_full_names\'], \'dbxrefs\': record[\'dbxrefs\'], \'organism\': record[\'organism\'], \'source\': record[\'source\'], \'source_url\': record[\'source_url\']'

// db.query is called twice per stage now (a cheap LIMIT 1 existence probe, then the real
// page fetch) - keying the mock by query text (which stage it belongs to) rather than call
// order/count means both calls for the stage that "wins" naturally return the same data,
// matching real behavior, without hand-sequencing mockResolvedValueOnce per call.
function mockDbQueryByStage (stageResults: { exact?: any[], prefix?: any[], fuzzy?: any[] }): void {
  jest.spyOn(dbModule.db, 'query').mockImplementation(async (query: unknown) => {
    const text = String(query)
    let result: any[] = []
    if (text.includes('LEVENSHTEIN_MATCH')) {
      result = stageResults.fuzzy ?? []
    } else if (text.includes('STARTS_WITH')) {
      result = stageResults.prefix ?? []
    } else {
      result = stageResults.exact ?? []
    }
    return { all: async () => result } as any
  })
}

describe('proteinsRouters.proteins', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns protein by protein_id', async () => {
    const mockRecord = [{
      _id: 'P1',
      name: 'ProteinA',
      uniprot_names: ['ProteinA'],
      uniprot_full_names: ['FullProteinA'],
      dbxrefs: [{ name: 'UniProt', id: 'UP1' }],
      organism: 'Homo sapiens',
      source: 'UniProt',
      source_url: 'url'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockRecord)
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue(mockDBReturnStatements)

    const input = { protein_id: 'P1', page: 0 }
    const result = await proteinsRouters.proteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockRecord)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('returns proteins by name (exact match)', async () => {
    const mockResult = [{
      _id: 'P2',
      name: 'ProteinB',
      uniprot_names: ['ProteinB'],
      uniprot_full_names: ['FullProteinB'],
      dbxrefs: [{ name: 'UniProt', id: 'UP2' }],
      organism: 'Homo sapiens',
      source: 'UniProt',
      source_url: 'url'
    }]
    const querySpy = jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue(mockDBReturnStatements)
    const getFilterStatementsSpy = jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')

    const input = { name: 'ProteinB', page: 0 }
    const result = await proteinsRouters.proteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalled()

    // Verify getFilterStatements was called with the correct parameters
    // After name is deleted, input only contains { page: 0, organism: 'Homo sapiens' }
    expect(getFilterStatementsSpy).toHaveBeenCalled()
    const filterCall = getFilterStatementsSpy.mock.calls[0]
    expect(filterCall[1]).toEqual({ page: 0, organism: 'Homo sapiens' }) // input after name is deleted

    // Verify the query contains the correct filter for name parameter
    // The router converts name to uppercase and creates: "PROTEINB" == record.name
    const queryString = querySpy.mock.calls[0][0] as string
    expect(queryString).toContain('"PROTEINB" == record.name')
    expect(queryString).toContain('FILTER')
  })

  it('returns proteins by uniprot_full_name (exact match)', async () => {
    const mockResult = [{
      _id: 'P3',
      name: 'ProteinC',
      uniprot_names: ['ProteinC'],
      uniprot_full_names: ['FullProteinC'],
      dbxrefs: [{ name: 'UniProt', id: 'UP3' }],
      organism: 'Homo sapiens',
      source: 'UniProt',
      source_url: 'url'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue(mockDBReturnStatements)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')

    const input = { uniprot_full_name: 'FullProteinC', page: 0 }
    const result = await proteinsRouters.proteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('returns proteins by dbxrefs (exact match)', async () => {
    const mockResult = [{
      _id: 'P4',
      name: 'ProteinD',
      uniprot_names: ['ProteinD'],
      uniprot_full_names: ['FullProteinD'],
      dbxrefs: [{ name: 'UniProt', id: 'UP4' }],
      organism: 'Homo sapiens',
      source: 'UniProt',
      source_url: 'url'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue(mockDBReturnStatements)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')

    const input = { dbxrefs: 'UP4', page: 0 }
    const result = await proteinsRouters.proteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('returns proteins by prefix search if exact match returns empty', async () => {
    const mockRecord = {
      _id: 'P5',
      name: 'ProteinE',
      uniprot_names: ['ProteinE'],
      uniprot_full_names: ['FullProteinE'],
      dbxrefs: [{ name: 'UniProt', id: 'UP5' }],
      organism: 'Homo sapiens',
      source: 'UniProt',
      source_url: 'url'
    }
    mockDbQueryByStage({ prefix: [mockRecord] })
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue(mockDBReturnStatements)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')

    const input = { uniprot_name: 'ProteinE', page: 0 }
    const result = await proteinsRouters.proteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual([mockRecord])
  })

  it('returns proteins by fuzzy search if prefix search returns empty', async () => {
    const mockRecord = {
      _id: 'P6',
      name: 'ProteinF',
      uniprot_names: ['ProteinF'],
      uniprot_full_names: ['FullProteinF'],
      dbxrefs: [{ name: 'UniProt', id: 'UP5' }],
      organism: 'Homo sapiens',
      source: 'UniProt',
      source_url: 'url'
    }
    mockDbQueryByStage({ fuzzy: [mockRecord] })
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue(mockDBReturnStatements)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')

    const input = { uniprot_full_name: 'ProteinF', page: 0 }
    const result = await proteinsRouters.proteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual([mockRecord])
  })

  it('respects limit and does not overlap or skip rows across pages (exact match)', async () => {
    // 11 exact matches total (e.g. CTCF across organisms/isoforms) - limit=5 must be honored,
    // and paging through must not repeat/skip rows or silently fall back to QUERY_LIMIT.
    const allMatches = Array.from({ length: 11 }, (_, i) => ({ _id: `P${i}`, name: 'CTCF', organism: 'Homo sapiens', source: 'UniProt', source_url: 'url' }))
    jest.spyOn(dbModule.db, 'query').mockImplementation(async (query: unknown) => {
      const text = String(query)
      const offsetLimitMatch = /LIMIT (\d+), (\d+)/.exec(text)
      let offset = 0
      let limit = allMatches.length
      if (offsetLimitMatch) {
        offset = Number(offsetLimitMatch[1])
        limit = Number(offsetLimitMatch[2])
      } else {
        const plainLimitMatch = /LIMIT (\d+)\b/.exec(text)
        if (plainLimitMatch) {
          limit = Number(plainLimitMatch[1])
        }
      }
      return { all: async () => allMatches.slice(offset, offset + limit) } as any
    })
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue(mockDBReturnStatements)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')

    const callPage = async (page: number): Promise<any> => {
      const input = { name: 'CTCF', page, limit: 5 }
      return await proteinsRouters.proteins({ input, ctx: {}, type: 'query', path: '', rawInput: input })
    }

    const page0 = await callPage(0)
    const page1 = await callPage(1)
    const page2 = await callPage(2)
    const page3 = await callPage(3)

    expect(page0).toHaveLength(5)
    expect(page1).toHaveLength(5)
    expect(page2).toHaveLength(1)
    expect(page3).toHaveLength(0)
    const ids = [...page0, ...page1, ...page2].map((r: any) => r._id)
    expect(new Set(ids).size).toBe(11)
  })

  it('sorts the exact-match and search-view stages with a deterministic tiebreaker', async () => {
    // Regression guard, same bug class as the ontology_terms pagination fix: record.chr isn't
    // even a field on this collection (every row ties on `undefined`), and BM25(record) DESC
    // alone ties whenever multiple records match equally well. probeThenFetchPage runs a
    // separate query execution per page, so an untied SORT can place a row in the overlapping
    // edge of two different pages (or skip it from both).
    const queries: string[] = []
    jest.spyOn(dbModule.db, 'query').mockImplementation(async (query: unknown) => {
      queries.push(String(query))
      return { all: async () => [] } as any
    })
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue(mockDBReturnStatements)

    const input = { name: 'SAM', page: 0, limit: 10 }
    await proteinsRouters.proteins({ input, ctx: {}, type: 'query', path: '', rawInput: input })

    const exactQuery = queries.find(q => !q.includes('STARTS_WITH') && !q.includes('LEVENSHTEIN_MATCH'))
    expect(exactQuery).toContain('SORT record._key')

    const prefixQuery = queries.find(q => q.includes('STARTS_WITH'))
    expect(prefixQuery).toContain('SORT BM25(record) DESC, record._key')
  })

  it('caps limit to MAX_PAGE_SIZE', async () => {
    const mockRecord = {
      _id: 'P7',
      name: 'ProteinG',
      uniprot_names: ['ProteinG'],
      uniprot_full_names: ['FullProteinG'],
      dbxrefs: [{ name: 'UniProt', id: 'UP5' }],
      organism: 'Homo sapiens',
      source: 'UniProt',
      source_url: 'url'
    }
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([mockRecord])
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue(mockDBReturnStatements)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')

    const input = { name: 'ProteinG', page: 0, limit: 1000 }
    const result = await proteinsRouters.proteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual([mockRecord])
    expect(dbModule.db.query).toHaveBeenCalled()
  })
})
