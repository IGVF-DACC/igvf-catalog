import { drugsRouters } from '../../../datatypeRouters/nodes/drugs'
import * as dbModule from '../../../../database'
import * as helpers from '../../../datatypeRouters/_helpers'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')
jest.mock('../../../datatypeRouters/_helpers')

describe('drugsRouters.drugs', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns a drug by ID', async () => {
    const mockRecord = { _id: '1', name: 'DrugA', source: 'src', source_url: 'url' }
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([mockRecord])
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name, source, source_url')

    const input = { drug_id: '1' }
    const result = await drugsRouters.drugs({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockRecord)
  })

  it('returns drugs by token search', async () => {
    const mockRecords = [
      { _id: '2', name: 'DrugB', source: 'src', source_url: 'url' }
    ]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockRecords)
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name, source, source_url')

    const input = { name: 'DrugB', page: 0 }
    const result = await drugsRouters.drugs({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockRecords)
  })

  it('returns drugs by fuzzy search if token search is empty', async () => {
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any) // tokenQuery returns []
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ _id: '3', name: 'DrugC', source: 'src', source_url: 'url' }]) } as any) // fuzzyQuery returns result
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name, source, source_url')

    const input = { name: 'DrugC', page: 0 }
    const result = await drugsRouters.drugs({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual([{ _id: '3', name: 'DrugC', source: 'src', source_url: 'url' }])
  })

  it('throws BAD_REQUEST if neither drug_id nor name is defined', async () => {
    await expect(
      drugsRouters.drugs({
        input: { page: 0 },
        ctx: {},
        type: 'query',
        path: '',
        rawInput: { page: 0 }
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws NOT_FOUND if drug_id not found', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name, source, source_url')

    const input = { drug_id: 'notfound' }
    await expect(
      drugsRouters.drugs({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('caps limit to MAX_PAGE_SIZE', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([{ _id: '4', name: 'DrugD', source: 'src', source_url: 'url' }])
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name, source, source_url')

    const input = { name: 'DrugD', page: 0, limit: 1000 }
    const result = await drugsRouters.drugs({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual([{ _id: '4', name: 'DrugD', source: 'src', source_url: 'url' }])
  })
})
