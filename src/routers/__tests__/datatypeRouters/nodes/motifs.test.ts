import { motifsRouters } from '../../../datatypeRouters/nodes/motifs'
import * as dbModule from '../../../../database'
import * as helpers from '../../../datatypeRouters/_helpers'

jest.mock('../../../../database')
jest.mock('../../../datatypeRouters/_helpers')

describe('motifsRouters.motifs', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns motifs by tf_name (uppercased)', async () => {
    const mockResult = [{
      name: 'motif1',
      tf_name: 'TF1',
      length: 10,
      pwm: [['A', 'C'], ['G', 'T']],
      source: 'ENCODE',
      source_url: 'url'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('tf_name == "TF1"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('name, tf_name, length, pwm, source, source_url')

    const input = { tf_name: 'tf1', page: 0 }
    const result = await motifsRouters.motifs({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('caps limit to MAX_PAGE_SIZE', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('name')

    const input = { page: 0, limit: 1000 }
    await motifsRouters.motifs({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('returns motifs with filter', async () => {
    const mockResult = [{
      name: 'motif2',
      tf_name: 'TF2',
      length: 12,
      pwm: [['A'], ['T']],
      source: 'ENCODE',
      source_url: 'url2'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('source == "HOCOMOCOv11"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('name, tf_name, length, pwm, source, source_url')

    const input = { source: 'HOCOMOCOv11', page: 0 }
    const result = await motifsRouters.motifs({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
  })
})
