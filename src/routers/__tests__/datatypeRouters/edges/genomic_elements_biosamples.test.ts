import { genomicElementsBiosamplesRouters } from '../../../datatypeRouters/edges/genomic_elements_biosamples'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('genomicElementsBiosamplesRouters.biosamplesFromGenomicElements', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns biosamples for genomic elements matching a region filter', async () => {
    const mockResult = [
      {
        log2FC: 1.5,
        strand: '+',
        neg_log10_pvalue: 3.2,
        neg_log10_pvalue_adj: 2.8,
        DNA_count: 120,
        RNA_count: 80,
        significant: true,
        source: 'ENCODE',
        source_url: 'http://example.com/mpra',
        genomic_element: 'genomic_elements/GE1',
        biosample: 'ontology_terms/CL_0000001',
        name: 'expression effect in',
        class: 'observed data',
        method: 'MPRA',
        files_filesets: 'files_filesets/FILESET1'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { region: 'chr1:1000-2000', method: 'MPRA', page: 0 }
    const result = await genomicElementsBiosamplesRouters.biosamplesFromGenomicElements({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST if no genomic element, method, source or fileset filter is provided', async () => {
    const input = { page: 0 } as any
    await expect(
      genomicElementsBiosamplesRouters.biosamplesFromGenomicElements({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST if method is invalid', async () => {
    const input = { method: 'NOT_A_METHOD', page: 0 } as any
    await expect(
      genomicElementsBiosamplesRouters.biosamplesFromGenomicElements({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST if source is invalid', async () => {
    const input = { source: 'NOT_A_SOURCE', page: 0 } as any
    await expect(
      genomicElementsBiosamplesRouters.biosamplesFromGenomicElements({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('genomicElementsBiosamplesRouters.genomicElementsFromBiosamples', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns genomic elements for a biosample_name filter', async () => {
    const mockResult = [
      {
        log2FC: -0.8,
        strand: '-',
        neg_log10_pvalue: 1.1,
        neg_log10_pvalue_adj: 0.9,
        DNA_count: 55,
        RNA_count: 40,
        significant: false,
        source: 'IGVF',
        source_url: 'http://example.com/mpra2',
        genomic_element: 'genomic_elements/GE2',
        biosample: 'ontology_terms/CL_0000182',
        name: 'has expression effect from',
        class: 'observed data',
        method: 'MPRA',
        files_filesets: 'files_filesets/FILESET2'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { biosample_name: 'liver', page: 0 }
    const result = await genomicElementsBiosamplesRouters.genomicElementsFromBiosamples({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST if no biosample, method, source or fileset filter is provided', async () => {
    const input = { page: 0 } as any
    await expect(
      genomicElementsBiosamplesRouters.genomicElementsFromBiosamples({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST if source is invalid', async () => {
    const input = { source: 'NOT_A_SOURCE', page: 0 } as any
    await expect(
      genomicElementsBiosamplesRouters.genomicElementsFromBiosamples({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
