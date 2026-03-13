import { genomicRegionsRouters } from '../../../datatypeRouters/nodes/genomic_elements'
import * as dbModule from '../../../../database'
import * as helpers from '../../../datatypeRouters/_helpers'

jest.mock('../../../../database')
jest.mock('../../../datatypeRouters/_helpers')

describe('genomicRegionsRouters.genomicElements', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns genomic elements for human by default', async () => {
    const mockResult = [{
      chr: 'chr1',
      start: 100,
      end: 200,
      name: 'element1',
      source_annotation: 'ann1',
      type: 'enhancer',
      source: 'ENCODE',
      source_url: 'url'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'preProcessRegionParam').mockImplementation(input => input)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('chr == "chr1"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('chr, start, end, name, source_annotation, type, source, source_url')

    const input = { chr: 'chr1', page: 0 }
    const result = await genomicRegionsRouters.genomicElements({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('returns genomic elements for mouse if organism is Mus musculus', async () => {
    const mockResult = [{
      chr: 'chr2',
      start: 300,
      end: 400,
      name: 'element2',
      source_annotation: 'ann2',
      type: 'promoter',
      source: 'ENCODE',
      source_url: 'url2'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'preProcessRegionParam').mockImplementation(input => input)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('chr == "chr2"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('chr, start, end, name, source_annotation, type, source, source_url')

    const input = { organism: 'Mus musculus', chr: 'chr2', page: 0 }
    const result = await genomicRegionsRouters.genomicElements({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalled()
  })
})
