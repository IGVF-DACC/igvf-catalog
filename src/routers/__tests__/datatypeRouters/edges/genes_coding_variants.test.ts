import { genesCodingVariantsRouters } from '../../../datatypeRouters/edges/genes_coding_variants'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('genesCodingVariantsRouters.codingVariantsFromGenes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns coding variants scores for a gene', async () => {
    const mockResult = [{
      variant: 'var1',
      scores: [
        { source: 'SGE', score: 1.2 },
        { source: 'VAMP-seq', score: 0.8 }
      ]
    }]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(undefined) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(mockResult) } as any)

    const input = { gene_id: 'GENE1', page: 0 }
    const result = await genesCodingVariantsRouters.codingVariantsFromGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('returns cached values if present', async () => {
    const cachedResult = [
      { variant: 'cachedVar', scores: [{ source: 'SGE', score: 2.1 }] }
    ]
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([cachedResult]) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue([]) } as any)

    const input = { gene_id: 'GENE2', page: 0 }
    const result = await genesCodingVariantsRouters.codingVariantsFromGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(cachedResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST if gene_id is missing', async () => {
    const input = { page: 0 } as any
    await expect(
      genesCodingVariantsRouters.codingVariantsFromGenes({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('genesCodingVariantsRouters.allCodingVariantsFromGenes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns all coding variant scores for a gene and dataset', async () => {
    const mockScores = [1.1, 2.2, 3.3]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockScores)
    } as any)

    const input = { gene_id: 'GENE3', dataset: 'SGE', page: 0 }
    const result = await genesCodingVariantsRouters.allCodingVariantsFromGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockScores)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('throws BAD_REQUEST if gene_id is missing', async () => {
    const input = { dataset: 'SGE', page: 0 } as any
    await expect(
      genesCodingVariantsRouters.allCodingVariantsFromGenes({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST if dataset is invalid', async () => {
    const input = { gene_id: 'GENE4', dataset: 'INVALID', page: 0 }
    await expect(
      genesCodingVariantsRouters.allCodingVariantsFromGenes({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
