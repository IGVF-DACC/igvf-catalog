import { enhancerGenePredictionsRouters } from '../../../datatypeRouters/edges/enhancer_genes'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('enhancerGenePredictionsRouters.enhancerGenePredictions', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns enhancer-gene predictions for a gene_id', async () => {
    const geneSearchResult = [
      { _id: 'GENE1', name: 'GENE1', chr: 'chr1', start: 1000, end: 5000 }
    ]

    const mainQueryResult = [
      {
        gene: { name: 'GENE1', _id: 'genes/GENE1', start: 1000, end: 5000, chr: 'chr1' },
        elements: [
          {
            id: 'genomic_elements/GE1',
            cell_type: 'K562',
            score: 0.85,
            model: 'ENCODE-rE2G',
            dataset: 'http://example.com/dataset1',
            element_type: 'enhancer',
            element_chr: 'chr1',
            element_start: 1200,
            element_end: 1400,
            name: 'predicted to regulate',
            class: 'observed data',
            method: 'ENCODE-rE2G',
            files_filesets: 'files_filesets/FILESET1'
          }
        ]
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(geneSearchResult) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(mainQueryResult) } as any)

    const input = { gene_id: 'GENE1', page: 0 }
    const result = await enhancerGenePredictionsRouters.enhancerGenePredictions({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mainQueryResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('returns predictions filtered only by method when no gene identifier is provided', async () => {
    const mainQueryResult = [
      {
        gene: { name: 'GENE2', _id: 'genes/GENE2', start: 2000, end: 6000, chr: 'chr2' },
        elements: [
          {
            id: 'genomic_elements/GE2',
            cell_type: 'HepG2',
            score: 0.5,
            model: 'scE2G',
            dataset: 'http://example.com/dataset2',
            element_type: 'enhancer',
            element_chr: 'chr2',
            element_start: 2200,
            element_end: 2400,
            name: 'predicted to regulate',
            class: 'observed data',
            method: 'scE2G',
            files_filesets: null
          }
        ]
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mainQueryResult)
    } as any)

    const input = { method: 'scE2G', page: 0 } as any
    const result = await enhancerGenePredictionsRouters.enhancerGenePredictions({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mainQueryResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws NOT_FOUND if the gene_id does not match any gene', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)

    const input = { gene_id: 'DOES_NOT_EXIST', page: 0 }
    await expect(
      enhancerGenePredictionsRouters.enhancerGenePredictions({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws NOT_FOUND if no gene identifier, method or fileset filter is provided', async () => {
    const input = { page: 0 } as any
    await expect(
      enhancerGenePredictionsRouters.enhancerGenePredictions({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST if method is invalid', async () => {
    const input = { gene_id: 'GENE1', method: 'NOT_A_METHOD', page: 0 } as any
    await expect(
      enhancerGenePredictionsRouters.enhancerGenePredictions({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
