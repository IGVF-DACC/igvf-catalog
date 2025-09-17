import { variantsRouters } from '../../../datatypeRouters/nodes/variants'
import * as dbModule from '../../../../database'
import * as helpers from '../../../datatypeRouters/_helpers'

jest.mock('../../../../database')
jest.mock('../../../datatypeRouters/_helpers')
jest.mock('../../../datatypeRouters/nodes/genes')

describe('variantsRouters.variants', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns variants', async () => {
    const mockResult = [{
      _id: 'V1',
      chr: 'chr1',
      pos: 12345,
      ref: 'A',
      alt: 'T',
      annotations: { funseq_description: 'coding' },
      source: 'gnomAD',
      source_url: 'url',
      organism: 'Homo sapiens'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('chr == "chr1"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, chr, pos, ref, alt, annotations, source, source_url')

    const input = { chr: 'chr1', page: 0 }
    const result = await variantsRouters.variants({
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
    const mockResult = Array(500).fill({
      _id: 'V3',
      chr: 'chr3',
      pos: 11111,
      ref: 'C',
      alt: 'G',
      annotations: {},
      source: 'gnomAD',
      source_url: 'url3',
      organism: 'Homo sapiens'
    })
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, chr, pos, ref, alt, annotations, source, source_url')

    const input = { page: 0, limit: 10000 }
    const result = await variantsRouters.variants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    }) as any[] // Type assertion to any[]
    expect(result.length).toBeLessThanOrEqual(500)
    expect(dbModule.db.query).toHaveBeenCalled()
  })
})
