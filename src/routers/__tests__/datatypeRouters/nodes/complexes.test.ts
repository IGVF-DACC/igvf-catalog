import { complexesRouters } from '../../../datatypeRouters/nodes/complexes'
import * as dbModule from '../../../../database'
import * as helpers from '../../../datatypeRouters/_helpers'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')
jest.mock('../../../datatypeRouters/_helpers')

describe('complexesRouters.complexes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns a complex by ID', async () => {
    const mockRecord = { _id: '1', name: 'ComplexA', source: 'src', source_url: 'url', alias: null, molecules: null, evidence_code: null, experimental_evidence: null, description: null, complex_assembly: null, complex_source: null, reactome_xref: [] }
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([mockRecord])
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name, source, source_url')

    const input = { complex_id: '1' }
    const result = await complexesRouters.complexes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockRecord)
  })

  it('returns complexes by fuzzy name search', async () => {
    const mockRecords = [
      { _id: '2', name: 'ComplexB', source: 'src', source_url: 'url', alias: null, molecules: null, evidence_code: null, experimental_evidence: null, description: null, complex_assembly: null, complex_source: null, reactome_xref: [] }
    ]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockRecords)
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name, source, source_url')

    const input = { name: 'ComplexB', page: 0 }
    const result = await complexesRouters.complexes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockRecords)
  })

  it('returns complexes by fuzzy description search', async () => {
    const mockRecords = [
      { _id: '3', name: 'ComplexC', description: 'desc', source: 'src', source_url: 'url', alias: null, molecules: null, evidence_code: null, experimental_evidence: null, complex_assembly: null, complex_source: null, reactome_xref: [] }
    ]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockRecords)
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name, description, source, source_url')

    const input = { description: 'desc', page: 0 }
    const result = await complexesRouters.complexes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockRecords)
  })

  it('throws NOT_FOUND if complex_id not found', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name, source, source_url')

    const input = { complex_id: 'notfound' }
    await expect(
      complexesRouters.complexes({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST if no parameters are defined', async () => {
    await expect(
      complexesRouters.complexes({
        input: { page: 0 },
        ctx: {},
        type: 'query',
        path: '',
        rawInput: { page: 0 }
      })
    ).rejects.toThrow(TRPCError)
  })
})
