import { variantsVariantsRouters } from '../../../datatypeRouters/edges/variants_variants'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('variantsVariantsRouters.variantsFromVariantIDSummary', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns LD summary predictions for a variant_id', async () => {
    const variantSearchResult = [
      {
        _id: 'NC_000001.11:69633:TGT:GAA',
        chr: 'chr1',
        pos: 69633,
        rsid: ['rs123'],
        ref: 'TGT',
        alt: 'GAA',
        spdi: 'NC_000001.11:69633:TGT:GAA',
        hgvs: 'NC_000001.11:g.69634_69636delinsGAA',
        ca_id: null,
        annotations: {
          funseq_description: 'coding',
          cadd_rawscore: 1.5,
          cadd_phred: 12.3
        },
        source: 'FAVOR',
        source_url: 'http://example.com/favor',
        organism: null
      }
    ]

    const ldQueryResult = [
      {
        ancestry: 'EUR',
        d_prime: 0.9,
        r2: 0.95,
        'sequence variant': {
          _id: 'NC_000001.11:70000:A:G',
          chr: 'chr1',
          pos: 70000,
          rsid: ['rs456'],
          ref: 'A',
          alt: 'G',
          spdi: 'NC_000001.11:70000:A:G',
          hgvs: 'NC_000001.11:g.70000A>G',
          ca_id: null,
          predictions: {
            qtls: [
              { type: 'eQTL', cell_types: [{ name: 'liver', count: 2 }], genes: [{ name: 'GENE1', count: 2 }] }
            ],
            tf_binding: [
              { motif: 'CTCF', count: 3, cell_types: [{ cell_type: 'K562', count: 3 }] }
            ]
          }
        }
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(variantSearchResult) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(ldQueryResult) } as any)

    const input = { variant_id: 'NC_000001.11:69633:TGT:GAA', page: 0 }
    const result: any = await variantsVariantsRouters.variantsFromVariantIDSummary({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
    expect(result).toHaveLength(1)
    expect(result[0].ancestry).toBe('EUR')
    expect(result[0].d_prime).toBe(0.9)
    expect(result[0].r2).toBe(0.95)
    expect(result[0]['sequence variant'].pos).toBe(70000)
    expect(result[0]['sequence variant'].predictions).toBeUndefined()
    expect(result[0].predictions.qtls[0].type).toBe('eQTL')
    expect(result[0].predictions.tf_binding[0].motif).toBe('CTCF')
  })

  it('throws BAD_REQUEST if no identifying parameter is provided', async () => {
    const input = { page: 0 } as any
    await expect(
      variantsVariantsRouters.variantsFromVariantIDSummary({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws NOT_FOUND if the variant does not exist', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)

    const input = { variant_id: 'DOES_NOT_EXIST', page: 0 }
    await expect(
      variantsVariantsRouters.variantsFromVariantIDSummary({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('variantsVariantsRouters.variantsFromVariantID', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns LD records with merged variant position data for a variant_id', async () => {
    const variantIdSearchResult = ['variants/NC_000001.11:69633:TGT:GAA']

    const mainLdQueryResult = [
      {
        chr: 'chr1',
        ancestry: 'EUR',
        d_prime: 0.9,
        r2: 0.95,
        label: 'linkage disequilibrium',
        variant_1_base_pair: 'G:A',
        variant_1_rsid: 'rs1',
        variant_2_base_pair: 'T:C',
        variant_2_rsid: 'rs2',
        source: 'TopLD',
        source_url: 'http://example.com/topld',
        variant_1: 'variants/NC_000001.11:69633:TGT:GAA',
        variant_2: 'variants/NC_000001.11:70000:A:G',
        sequence_variant: 'NC_000001.11:70000:A:G',
        name: 'correlated with'
      }
    ]

    const variantDataResult = [
      { id: 'variants/NC_000001.11:69633:TGT:GAA', spdi: 'NC_000001.11:69633:TGT:GAA', hgvs: 'NC_000001.11:g.69634_69636delinsGAA', pos: 69633 },
      { id: 'variants/NC_000001.11:70000:A:G', spdi: 'NC_000001.11:70000:A:G', hgvs: 'NC_000001.11:g.70000A>G', pos: 70000 }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(variantIdSearchResult) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mainLdQueryResult) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(variantDataResult) } as any)

    const input = { variant_id: 'NC_000001.11:69633:TGT:GAA', page: 0 }
    const result: any = await variantsVariantsRouters.variantsFromVariantID({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(dbModule.db.query).toHaveBeenCalledTimes(3)
    expect(result).toHaveLength(1)
    expect(result[0].ancestry).toBe('EUR')
    expect(result[0].variant_1_pos).toBe(69633)
    expect(result[0].variant_1_spdi).toBe('NC_000001.11:69633:TGT:GAA')
    expect(result[0].variant_2_pos).toBe(70000)
    expect(result[0].variant_2_hgvs).toBe('NC_000001.11:g.70000A>G')
    expect(result[0].sequence_variant).toBe('NC_000001.11:70000:A:G')
  })

  it('throws BAD_REQUEST if no variant property is provided', async () => {
    const input = { page: 0 } as any
    await expect(
      variantsVariantsRouters.variantsFromVariantID({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST if r2 is not a number or range expression', async () => {
    const input = { variant_id: 'V1', r2: 'not-a-number', page: 0 } as any
    await expect(
      variantsVariantsRouters.variantsFromVariantID({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST if d_prime is not a number or range expression', async () => {
    const input = { variant_id: 'V1', d_prime: 'not-a-number', page: 0 } as any
    await expect(
      variantsVariantsRouters.variantsFromVariantID({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST if ancestry is not one of the allowed values', async () => {
    const input = { variant_id: 'V1', ancestry: 'NOT_A_REAL_ANCESTRY', page: 0 } as any
    await expect(
      variantsVariantsRouters.variantsFromVariantID({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
