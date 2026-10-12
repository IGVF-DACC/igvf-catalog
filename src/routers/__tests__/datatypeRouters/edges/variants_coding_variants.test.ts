import { variantsCodingVariantsRouters } from '../../../datatypeRouters/edges/variants_coding_variants'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('variantsCodingVariantsRouters.codingVariantsFromVariants', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns coding variants for a variant identified by spdi', async () => {
    const mockResult = [{
      _id: 'coding_variants/CV1',
      name: 'p.Cys203Glu',
      ref: 'C',
      alt: 'E',
      protein_name: 'BRCA1_HUMAN',
      protein_id: 'ENSP00000493376',
      gene_name: 'BRCA1',
      transcript_id: 'ENST00000641515',
      aapos: 203,
      hgvsp: 'p.Cys203Glu',
      hgvsc: 'c.607T>G',
      refcodon: 'TGT',
      codonpos: 1,
      SIFT_score: 0.01,
      SIFT4G_score: 0.02,
      Polyphen2_HDIV_score: 0.9,
      Polyphen2_HVAR_score: 0.85,
      VEST4_score: 0.7,
      REVEL_score: 0.6,
      MutPred_score: 0.5,
      BayesDel_addAF_score: 0.4,
      BayesDel_noAF_score: 0.3,
      VARITY_R_score: 0.2,
      VARITY_ER_score: 0.25,
      VARITY_R_LOO_score: 0.22,
      VARITY_ER_LOO_score: 0.24,
      ESM1b_score: -5.2,
      AlphaMissense_score: 0.8,
      CADD_raw_score: 3.5,
      source: 'dbNSFP',
      source_url: 'https://dbnsfp.org'
    }]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['variants/NC_000001.11:69633:TGT:GAA']) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mockResult) } as any)

    const input = { spdi: 'NC_000001.11:69633:TGT:GAA', page: 0 }
    const result = await variantsCodingVariantsRouters.codingVariantsFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('throws BAD_REQUEST if no variant identifying parameter is provided', async () => {
    const input = { page: 0 } as any
    await expect(
      variantsCodingVariantsRouters.codingVariantsFromVariants({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('variantsCodingVariantsRouters.variantsFromCodingVariants', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns variants for a coding variant search by gene name', async () => {
    const mockResult = [{
      _id: 'variants/NC_000001.11:69633:TGT:GAA',
      chr: 'chr1',
      pos: 69633,
      ref: 'TGT',
      alt: 'GAA',
      rsid: null,
      spdi: 'NC_000001.11:69633:TGT:GAA',
      hgvs: 'NC_000001.11:g.69634_69636delinsGAA',
      ca_id: null
    }]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { gene_name: 'BRCA1', page: 0 }
    const result = await variantsCodingVariantsRouters.variantsFromCodingVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST if no coding variant parameter is provided', async () => {
    const input = { page: 0 } as any
    await expect(
      variantsCodingVariantsRouters.variantsFromCodingVariants({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST if amino_acid_position is not a number', async () => {
    const input = { gene_name: 'BRCA1', amino_acid_position: 'abc', page: 0 }
    await expect(
      variantsCodingVariantsRouters.variantsFromCodingVariants({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
