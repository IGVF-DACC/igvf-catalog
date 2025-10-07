import { autocompleteRouters } from '../../datatypeRouters/autocomplete'
import * as dbModule from '../../../database'

jest.mock('../../../database')

describe('autocompleteRouters.autocomplete', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns autocomplete results for gene, disease, and protein', async () => {
    const mockResults = [
      { type: 'gene', term: 'BRCA1', uri: '/genes/GENE1' },
      { type: 'disease', term: 'Breast cancer', uri: '/ontology_terms/TERM1' },
      { type: 'protein', term: 'BRCA1', uri: '/proteins/PROT1' }
    ]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResults)
    } as any)

    const input = { term: 'brca', page: 0 }
    const result = await autocompleteRouters.autocomplete({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
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
      rawInput: input
    })
    expect(result).toEqual([])
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('handles pagination with page parameter', async () => {
    const mockResults = [
      { type: 'gene', term: 'GENE2', uri: '/genes/GENE2' }
    ]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResults)
    } as any)

    const input = { term: 'GENE', page: 2 }
    const result = await autocompleteRouters.autocomplete({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResults)
    expect(dbModule.db.query).toHaveBeenCalled()
  })
})
