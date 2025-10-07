import { pathwaysRouters, pathwaySearchPersistent, findPathwaysByTextSearch } from '../../../datatypeRouters/nodes/pathways'
import * as dbModule from '../../../../database'
import * as helpers from '../../../datatypeRouters/_helpers'

jest.mock('../../../../database')
jest.mock('../../../datatypeRouters/_helpers')

describe('pathwaysRouters.pathways', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns pathways by id', async () => {
    const mockResult = [{
      _id: '1',
      name: 'PathwayA',
      organism: 'Homo sapiens',
      source: 'Reactome',
      source_url: 'url',
      id_version: 'v1',
      is_in_disease: false,
      name_aliases: ['AliasA'],
      is_top_level_pathway: true,
      disease_ontology_terms: ['ontology_terms/DOID:1'],
      go_biological_process: 'ontology_terms:GO:1'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('_key == "1"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name, organism, source, source_url, id_version, is_in_disease, name_aliases, is_top_level_pathway, disease_ontology_terms, go_biological_process')

    const input = { id: '1', page: 0 }
    const result = await pathwaysRouters.pathways({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('returns pathways by name text search if persistent returns empty', async () => {
    const mockResult = [{
      _id: '2',
      name: 'PathwayB',
      organism: 'Homo sapiens',
      source: 'Reactome',
      source_url: 'url',
      id_version: 'v1',
      is_in_disease: false,
      name_aliases: ['AliasA'],
      is_top_level_pathway: true,
      disease_ontology_terms: ['ontology_terms/DOID:1'],
      go_biological_process: 'ontology_terms:GO:1'
    }]
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any) // persistent returns []
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mockResult) } as any) // text search returns result
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name')

    const input = { name: 'PathwayB', page: 0 }
    const result = await pathwaysRouters.pathways({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
  })

  it('returns pathways by name_aliases text search if persistent returns empty', async () => {
    const mockResult = [{
      _id: '3',
      name: 'PathwayC',
      organism: 'Homo sapiens',
      source: 'Reactome',
      source_url: 'url',
      id_version: 'v1',
      is_in_disease: false,
      name_aliases: ['AliasA'],
      is_top_level_pathway: true,
      disease_ontology_terms: ['ontology_terms/DOID:1'],
      go_biological_process: 'ontology_terms:GO:1'
    }]
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any) // persistent returns []
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mockResult) } as any) // text search returns result
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name')

    const input = { name_aliases: 'AliasC', page: 0 }
    const result = await pathwaysRouters.pathways({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
  })

  it('returns empty array if no results found', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name')

    const input = { page: 0 }
    const result = await pathwaysRouters.pathways({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual([])
  })

  it('caps limit to MAX_PAGE_SIZE in persistent search', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([{ _id: '4', name: 'PathwayD' }])
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name')

    const input = { page: 0, limit: 1000 }
    const result = await pathwaySearchPersistent(input)
    expect(result).toEqual([{ _id: '4', name: 'PathwayD' }])
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('formats ontology term inputs in persistent search', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([{ _id: '5', name: 'PathwayE', disease_ontology_terms: ['ontology_terms/DOID:2'], go_biological_process: 'ontology_terms/GO:2' }])
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name, disease_ontology_terms, go_biological_process')

    const input = { disease_ontology_terms: 'DOID:2', go_biological_process: 'GO:2', page: 0 }
    const result = await pathwaySearchPersistent(input)
    expect(result).toEqual([{ _id: '5', name: 'PathwayE', disease_ontology_terms: ['ontology_terms/DOID:2'], go_biological_process: 'ontology_terms/GO:2' }])
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('findPathwaysByTextSearch returns fuzzy results if no token results', async () => {
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any) // token search returns []
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ _id: '6', name: 'PathwayF' }]) } as any) // fuzzy search returns result
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name')

    const input = { name: 'PathwayF', page: 0 }
    const result = await findPathwaysByTextSearch(input, { db_collection_name: 'pathways' } as any)
    expect(result).toEqual([{ _id: '6', name: 'PathwayF' }])
  })
})
