import { genesCodingVariantsRouters } from '../../../datatypeRouters/edges/genes_coding_variants'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

describe('genesCodingVariantsRouters', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })
  describe('codingVariantsFromGenes', () => {
    it('throws if gene_id is missing', async () => {
      await expect(
        genesCodingVariantsRouters.codingVariantsFromGenes({ input: {} as any, ctx: {}, type: 'query', path: '', rawInput: {} })
      ).rejects.toThrow(TRPCError)
    })

    it('returns db results', async () => {
      const mockResult = [
        { variant: 'cv1', scores: [{ source: 'SGE', score: 1.2 }] }
      ]
      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { gene_id: 'GENE1', page: 0 }
      const result = await genesCodingVariantsRouters.codingVariantsFromGenes({ input, ctx: {}, type: 'query', path: '', rawInput: input })
      expect(result).toEqual(mockResult)
    })
  })

  describe('allCodingVariantsFromGenes', () => {
    it('throws if gene_id is missing', async () => {
      await expect(
        genesCodingVariantsRouters.allCodingVariantsFromGenes({ input: {} as any, ctx: {}, type: 'query', path: '', rawInput: {} })
      ).rejects.toThrow(TRPCError)
    })

    it('throws if dataset is invalid', async () => {
      await expect(
        genesCodingVariantsRouters.allCodingVariantsFromGenes({ input: { gene_id: 'GENE1', dataset: 'INVALID', page: 0 }, ctx: {}, type: 'query', path: '', rawInput: {} })
      ).rejects.toThrow(TRPCError)
    })

    it('returns db results', async () => {
      const mockResult = [1.1, 2.2, 3.3]
      jest.spyOn(dbModule.db, 'query').mockResolvedValue({
        all: jest.fn().mockResolvedValue(mockResult)
      } as any)

      const input = { gene_id: 'GENE1', dataset: 'SGE', page: 0 }
      const result = await genesCodingVariantsRouters.allCodingVariantsFromGenes({ input, ctx: {}, type: 'query', path: '', rawInput: input })
      expect(result).toEqual(mockResult)
    })
  })
})
