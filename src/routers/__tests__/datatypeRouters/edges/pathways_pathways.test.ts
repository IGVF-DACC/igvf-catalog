import { pathwaysPathwaysRouters } from '../../../datatypeRouters/edges/pathways_pathways'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('pathwaysPathwaysRouters.pathwaysFromPathways', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('resolves the pathway ID first, then queries related pathways (two sequential db calls)', async () => {
    const pathwayRecords = [{ _id: 'R-HSA-1971475', name: 'A pathway', organism: 'Homo sapiens' }]
    const mockResult = [
      {
        source: 'Reactome',
        source_url: 'https://reactome.org/',
        organism: 'Homo sapiens',
        class: 'biological relationship',
        method: null,
        label: null,
        files_filesets: 'files_filesets/IGVFFI8363VRKN',
        parent_pathway: 'pathways/R-HSA-1971475',
        child_pathway: 'pathways/R-HSA-1971476',
        name: 'parent of'
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(pathwayRecords) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(mockResult) } as any)

    const input = { pathway_id: 'R-HSA-1971475', page: 0 }
    const result = await pathwaysPathwaysRouters.pathwaysFromPathways({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('resolves pathways found by pathway_name, then queries related pathways', async () => {
    const pathwayRecords = [{ _id: 'R-HSA-1971475', name: 'Signal Transduction', organism: 'Homo sapiens' }]
    const mockResult = [
      {
        source: 'Reactome',
        source_url: 'https://reactome.org/',
        organism: 'Homo sapiens',
        class: 'biological relationship',
        method: null,
        label: null,
        files_filesets: 'files_filesets/IGVFFI8363VRKN',
        parent_pathway: 'pathways/R-HSA-1971474',
        child_pathway: 'pathways/R-HSA-1971475',
        name: 'child of'
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(pathwayRecords) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(mockResult) } as any)

    const input = { pathway_name: 'Signal Transduction', page: 0 }
    const result = await pathwaysPathwaysRouters.pathwaysFromPathways({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('returns an empty array when the pathway search resolves to no pathways', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)

    const input = { pathway_id: 'R-HSA-DOES-NOT-EXIST', page: 0 }
    const result = await pathwaysPathwaysRouters.pathwaysFromPathways({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual([])
  })

  it('throws BAD_REQUEST when no pathway property is defined', async () => {
    const input = { page: 0 } as any
    await expect(
      pathwaysPathwaysRouters.pathwaysFromPathways({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
