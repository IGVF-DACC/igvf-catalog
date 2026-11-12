import { autocompleteRouters } from '../../datatypeRouters/autocomplete'
import * as dbModule from '../../../database'

jest.mock('../../../database')

describe('autocompleteRouters.autocomplete', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns autocomplete results for genes', async () => {
    const mockResults = [
      { type: 'gene', term: 'BRCA1', name: 'BRCA1', uri: '/genes/GENE1' }
    ]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([mockResults])
    } as any)

    const input = { term: 'brca', page: 0 }
    const result = await autocompleteRouters.autocomplete({
      input,
      ctx: {},
      type: 'query',
      path: '',
      getRawInput: async () => input,
      signal: undefined,
      batchIndex: 0
    })
    expect(result).toEqual(mockResults)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('returns empty array if no matches found', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)

    const input = { term: 'notfound', page: 0 }
    const result = await autocompleteRouters.autocomplete({
      input,
      ctx: {},
      type: 'query',
      path: '',
      getRawInput: async () => input,
      signal: undefined,
      batchIndex: 0
    })
    expect(result).toEqual([])
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('handles pagination with page parameter', async () => {
    const mockResults = [
      { type: 'gene', term: 'GENE2', name: 'GENE2', uri: '/genes/GENE2' }
    ]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([mockResults])
    } as any)

    const input = { term: 'GENE', page: 2 }
    const result = await autocompleteRouters.autocomplete({
      input,
      ctx: {},
      type: 'query',
      path: '',
      getRawInput: async () => input,
      signal: undefined,
      batchIndex: 0
    })
    expect(result).toEqual(mockResults)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it.each([{ page: -1 }, { page: 0.5 }])('rejects an invalid page %j', async (overrides) => {
    const query = jest.spyOn(dbModule.db, 'query')
    const input = { term: 'GENE', ...overrides }
    await expect(autocompleteRouters.autocomplete({
      input,
      ctx: {},
      type: 'query',
      path: '',
      getRawInput: async () => input,
      signal: undefined,
      batchIndex: 0
    })).rejects.toThrow()
    expect(query).not.toHaveBeenCalled()
  })
})
