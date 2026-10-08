import { variantsBiosamplesRouters } from '../../../datatypeRouters/edges/variants_biosamples'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

const returnRecord = {
  variant: 'variants/NC_000001.11:69633:TGT:GAA',
  biosample: 'ontology_terms/EFO_0005292',
  genomic_element: null,
  strand: '+',
  log2FC: 0.4,
  DNA_count_ref: 10,
  DNA_count_alt: 12,
  RNA_count_ref: 8,
  RNA_count_alt: 15,
  postProbEffect: 0.95,
  CI_lower_95: 0.1,
  CI_upper_95: 0.9,
  significant: true,
  neg_log10_pvalue: 4.5,
  neg_log10_pvalue_adj: 4.0,
  label: 'variant-biosample',
  method: 'MPRA',
  class: 'observed data',
  source: 'IGVF',
  source_url: 'https://igvf.org',
  name: 'affects expression in',
  files_filesets: 'files_filesets/IGVFFI0001XXXX'
}

describe('variantsBiosamplesRouters.variantsFromBiosamples', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns variants for a biosample identified by biosample_id', async () => {
    const ontologyResult = [{
      _id: 'EFO_0005292',
      uri: 'https://uri/EFO_0005292',
      term_id: 'EFO_0005292',
      name: 'lymphoblastoid cell line'
    }]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(ontologyResult) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([returnRecord]) } as any)

    const input = { biosample_id: 'EFO_0005292', page: 0 }
    const result = await variantsBiosamplesRouters.variantsFromBiosamples({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual([returnRecord])
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('throws BAD_REQUEST when neither biosample_id nor biosample_name is provided', async () => {
    const input = { page: 0 }
    await expect(
      variantsBiosamplesRouters.variantsFromBiosamples({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('variantsBiosamplesRouters.biosamplesFromVariants', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns biosamples for a variant identified by spdi', async () => {
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['variants/NC_000001.11:69633:TGT:GAA']) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([returnRecord]) } as any)

    const input = { spdi: 'NC_000001.11:69633:TGT:GAA', page: 0 }
    const result = await variantsBiosamplesRouters.biosamplesFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual([returnRecord])
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('returns biosamples filtered only by method, without a variant lookup', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([{ ...returnRecord, method: 'STARR-seq' }])
    } as any)

    const input = { method: 'STARR-seq', page: 0 }
    const result = await variantsBiosamplesRouters.biosamplesFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual([{ ...returnRecord, method: 'STARR-seq' }])
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST when no variant property or method or files_fileset is provided', async () => {
    const input = { page: 0 }
    await expect(
      variantsBiosamplesRouters.biosamplesFromVariants({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
