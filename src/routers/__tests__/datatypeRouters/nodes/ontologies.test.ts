import { ontologyRouters } from '../../../datatypeRouters/nodes/ontologies'
import * as dbModule from '../../../../database'
import * as helpers from '../../../datatypeRouters/_helpers'

jest.mock('../../../../database')
jest.mock('../../../datatypeRouters/_helpers')

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
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
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

  it('returns fuzzy results if no exact match and name is provided', async () => {
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any) // exactMatchSearch returns []
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ uri: 'uri2', term_id: 'T2', name: 'Fuzzy Term' }]) } as any) // fuzzyTextSearch returns result
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
    expect(result).toEqual([{ uri: 'uri2', term_id: 'T2', name: 'Fuzzy Term' }])
  })

  it('returns fuzzy results if no exact match and description is provided', async () => {
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any) // exactMatchSearch returns []
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ uri: 'uri3', term_id: 'T3', name: 'Desc Term' }]) } as any) // fuzzyTextSearch returns result
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('uri, term_id, name')

    const input = { description: 'desc', page: 0 }
    const result = await ontologyRouters.ontologyTerm({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual([{ uri: 'uri3', term_id: 'T3', name: 'Desc Term' }])
  })

  it('caps limit to MAX_PAGE_SIZE', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)
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
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)
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
})
