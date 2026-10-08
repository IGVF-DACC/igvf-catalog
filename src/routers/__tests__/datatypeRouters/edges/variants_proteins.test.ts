import { variantsProteinsRouters } from '../../../datatypeRouters/edges/variants_proteins'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('variantsProteinsRouters.variantsFromProteins', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns proteins/complexes bound by a variant filtered by method', async () => {
    const mockResult = [
      {
        sequence_variant: 'variants/NC_000015.10:75202391:C:G',
        protein_complex: 'proteins/ENSP00000281043',
        name: 'modulates binding of',
        is_complex: false,
        method: 'ADASTRA',
        biosample_term: 'ontology_terms/EFO_0002069',
        score: -0.0171981040581793,
        motif: 'motifs/TFDP1_HUMAN_HOCOMOCOv11',
        motif_log2FC: -0.2727347850176788
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { method: 'ADASTRA', page: 0 }
    const result = await variantsProteinsRouters.variantsFromProteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('resolves protein/complex IDs first when protein_id is given (two sequential db calls)', async () => {
    const proteinComplexIDs = [['proteins/ENSP00000281043']]
    const mockResult = [
      {
        sequence_variant: 'variants/NC_000015.10:75202391:C:G',
        protein_complex: 'proteins/ENSP00000281043',
        name: 'modulates binding of',
        is_complex: false,
        method: 'ADASTRA',
        source: 'ADASTRA'
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(proteinComplexIDs) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(mockResult) } as any)

    const input = { protein_id: 'ENSP00000281043', page: 0 }
    const result = await variantsProteinsRouters.variantsFromProteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('throws BAD_REQUEST when no protein/method/files_fileset filter is defined', async () => {
    const input = { page: 0 } as any
    await expect(
      variantsProteinsRouters.variantsFromProteins({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('variantsProteinsRouters.proteinsFromVariants', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns proteins/complexes bound to a variant filtered by method', async () => {
    const mockResult = [
      {
        sequence_variant: 'variants/NC_000015.10:75202391:C:G',
        protein_complex: 'proteins/ENSP00000281043',
        name: 'modulates binding of',
        is_complex: false,
        method: 'ADASTRA'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { method: 'ADASTRA', page: 0 }
    const result = await variantsProteinsRouters.proteinsFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('resolves variant IDs first when variant_id is given (two sequential db calls)', async () => {
    const variantIDs = ['variants/NC_000015.10:75202391:C:G']
    const mockResult = [
      {
        sequence_variant: 'variants/NC_000015.10:75202391:C:G',
        protein_complex: 'proteins/ENSP00000281043',
        name: 'binding modulated by',
        is_complex: false,
        method: 'ADASTRA'
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(variantIDs) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(mockResult) } as any)

    const input = { variant_id: 'NC_000015.10:75202391:C:G', page: 0 }
    const result = await variantsProteinsRouters.proteinsFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('throws BAD_REQUEST when no variant/method/files_fileset filter is defined', async () => {
    const input = { page: 0 } as any
    await expect(
      variantsProteinsRouters.proteinsFromVariants({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
