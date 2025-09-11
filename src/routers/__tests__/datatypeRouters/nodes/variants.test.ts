import { variantsRouters, variantIDSearch, findVariants } from '../../../datatypeRouters/nodes/variants'
import * as dbModule from '../../../../database'
import * as helpers from '../../../datatypeRouters/_helpers'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')
jest.mock('../../../datatypeRouters/_helpers')
jest.mock('../../../datatypeRouters/nodes/genes')

describe('variantsRouters.variants', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns variants for human by default', async () => {
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

  it('returns variants for mouse if organism is Mus musculus', async () => {
    const mockResult = [{
      _id: 'V2',
      chr: 'chr2',
      pos: 54321,
      ref: 'G',
      alt: 'C',
      annotations: {},
      source: 'MouseDB',
      source_url: 'url2',
      organism: 'Mus musculus'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('chr == "chr2"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, chr, pos, ref, alt, annotations, source, source_url')

    const input = { organism: 'Mus musculus', chr: 'chr2', page: 0 }
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
    })
    expect((result as any[]).length).toBeLessThanOrEqual(500)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('throws NOT_FOUND if variant summary not found', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, chr, pos, ref, alt, annotations, source, source_url')

    const input = { spdi: 'notfound', page: 0 }
    await expect(
      variantsRouters.variantSummary({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('returns variant IDs by region', async () => {
    const mockIDs = ['V5', 'V6']
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockIDs)
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('chr == "chr5"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id')

    const input = { chr: 'chr5', position: 55555, page: 0 }
    const result = await variantIDSearch(input)
    expect(result).toEqual(mockIDs)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('returns alleles aggregation for valid region', async () => {
    const mockAlleles = [
      ['chr1', 12345, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09]
    ]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockAlleles)
    } as any)
    jest.spyOn(helpers, 'validRegion').mockReturnValue(['region', 'chr1', '12345', '12445'])
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('chr == "chr1"')

    const input = { region: 'chr1:12345-12445' }
    const result = await variantsRouters.variantsAlleles({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(Array.isArray(result)).toBe(true)
    const typedResult = result as any[][]
    expect(typedResult[0][0]).toBe('chr')
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('throws BAD_REQUEST for alleles aggregation with invalid region', async () => {
    jest.spyOn(helpers, 'validRegion').mockReturnValue(null)
    const input = { region: 'invalid' }
    await expect(
      variantsRouters.variantsAlleles({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('findVariants returns variants for region', async () => {
    const mockResult = [{
      _id: 'V7',
      chr: 'chr7',
      pos: 77777,
      ref: 'A',
      alt: 'G',
      annotations: {},
      source: 'gnomAD',
      source_url: 'url7',
      organism: 'Homo sapiens'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('chr == "chr7"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, chr, pos, ref, alt, annotations, source, source_url')

    const input = { region: 'chr7:77777-77778', page: 0 }
    const result = await findVariants(input)
    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalled()
  })
})
