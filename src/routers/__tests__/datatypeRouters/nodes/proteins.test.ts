import { proteinsRouters } from '../../../datatypeRouters/nodes/proteins'
import * as dbModule from '../../../../database'
import * as helpers from '../../../datatypeRouters/_helpers'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')
jest.mock('../../../datatypeRouters/_helpers')

describe('proteinsRouters.proteins', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns protein by protein_id', async () => {
    const mockRecord = {
      _id: 'P1',
      names: ['ProteinA'],
      full_names: ['FullProteinA'],
      dbxrefs: [{ name: 'UniProt', id: 'UP1' }],
      organism: 'Homo sapiens',
      source: 'UniProt',
      source_url: 'url'
    }
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([mockRecord])
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, names, full_names, dbxrefs, organism, source, source_url')

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
      names: ['ProteinB'],
      full_names: ['FullProteinB'],
      dbxrefs: [{ name: 'UniProt', id: 'UP2' }],
      organism: 'Homo sapiens',
      source: 'UniProt',
      source_url: 'url'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, names, full_names, dbxrefs, organism, source, source_url')
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('names == "PROTEINB"')

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
  })

  it('returns proteins by full_name (exact match)', async () => {
    const mockResult = [{
      _id: 'P3',
      names: ['ProteinC'],
      full_names: ['FullProteinC'],
      dbxrefs: [{ name: 'UniProt', id: 'UP3' }],
      organism: 'Homo sapiens',
      source: 'UniProt',
      source_url: 'url'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, names, full_names, dbxrefs, organism, source, source_url')
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('full_names == "FullProteinC"')

    const input = { full_name: 'FullProteinC', page: 0 }
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
      names: ['ProteinD'],
      full_names: ['FullProteinD'],
      dbxrefs: [{ name: 'UniProt', id: 'UP4' }],
      organism: 'Homo sapiens',
      source: 'UniProt',
      source_url: 'url'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, names, full_names, dbxrefs, organism, source, source_url')
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('dbxrefs.id == "UP4"')

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
      names: ['ProteinE'],
      full_names: ['FullProteinE'],
      dbxrefs: [{ name: 'UniProt', id: 'UP5' }],
      organism: 'Homo sapiens',
      source: 'UniProt',
      source_url: 'url'
    }
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any) // exact match returns []
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mockRecord) } as any) // prefix search returns result
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, names')
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')

    const input = { name: 'ProteinE', page: 0 }
    const result = await proteinsRouters.proteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockRecord)
  })

  it('returns proteins by fuzzy search if prefix search returns empty', async () => {
    const mockRecord = {
      _id: 'P6',
      names: ['ProteinF'],
      full_names: ['FullProteinF'],
      dbxrefs: [{ name: 'UniProt', id: 'UP5' }],
      organism: 'Homo sapiens',
      source: 'UniProt',
      source_url: 'url'
    }
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any) // exact match returns []
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any) // prefix search returns []
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mockRecord) } as any) // fuzzy search returns result
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, names')
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')

    const input = { name: 'ProteinF', page: 0 }
    const result = await proteinsRouters.proteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockRecord)
  })

  it('caps limit to MAX_PAGE_SIZE', async () => {
    const mockRecord = {
      _id: 'P7',
      names: ['ProteinG'],
      full_names: ['FullProteinG'],
      dbxrefs: [{ name: 'UniProt', id: 'UP5' }],
      organism: 'Homo sapiens',
      source: 'UniProt',
      source_url: 'url'
    }
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockRecord)
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, names')
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')

    const input = { name: 'ProteinG', page: 0, limit: 1000 }
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

  it('throws NOT_FOUND if protein_id not found', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([undefined])
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, names')

    const input = { protein_id: 'notfound', page: 0 }
    await expect(
      proteinsRouters.proteins({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
