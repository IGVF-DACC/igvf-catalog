import { variantsDrugsRouters } from '../../../datatypeRouters/edges/variants_drugs'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('variantsDrugsRouters.variantsFromDrugs', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns variants for a drug_id', async () => {
    const mockResult = [
      {
        _to: 'drugs/DRUG1',
        gene_symbol: ['CYP2D6'],
        pmid: '12345678',
        study_parameters: [
          {
            study_parameter_id: 'SP1',
            study_type: 'case-control',
            study_cases: '100',
            study_controls: '100',
            'p-value': '0.001',
            biogeographical_groups: 'European'
          }
        ],
        phenotype_categories: ['Toxicity'],
        source: 'pharmGKB',
        source_url: 'https://api.pharmgkb.org/v1/data/annotation/1',
        name: 'associated with',
        class: 'observed data',
        method: null,
        files_filesets: null,
        sequence_variant: 'variants/NC_000001.11:69633:TGT:GAA'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { drug_id: 'DRUG1', page: 0 }
    const result: any = await variantsDrugsRouters.variantsFromDrugs({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
    expect(result).toHaveLength(1)
    expect(result[0].drug).toBe('drugs/DRUG1')
    expect(result[0].sequence_variant).toBe('variants/NC_000001.11:69633:TGT:GAA')
    expect(result[0].phenotype_categories).toEqual(['Toxicity'])
  })

  it('throws BAD_REQUEST if no drug identifying property is provided', async () => {
    const input = { pmid: '12345', page: 0 } as any
    await expect(
      variantsDrugsRouters.variantsFromDrugs({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST if phenotype_categories is invalid', async () => {
    const input = { drug_id: 'DRUG1', phenotype_categories: 'NOT_A_CATEGORY', page: 0 } as any
    await expect(
      variantsDrugsRouters.variantsFromDrugs({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('variantsDrugsRouters.drugsFromVariants', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns drugs for a variant_id', async () => {
    const variantIdSearchResult = ['variants/NC_000001.11:69633:TGT:GAA']

    const mockResult = [
      {
        _from: 'variants/NC_000001.11:69633:TGT:GAA',
        gene_symbol: ['CYP2D6'],
        pmid: '12345678',
        study_parameters: [
          {
            study_parameter_id: 'SP1',
            study_type: 'case-control',
            study_cases: '100',
            study_controls: '100',
            'p-value': '0.001',
            biogeographical_groups: 'European'
          }
        ],
        phenotype_categories: ['Toxicity'],
        source: 'pharmGKB',
        source_url: 'https://api.pharmgkb.org/v1/data/annotation/1',
        name: 'associated with',
        class: 'observed data',
        method: null,
        files_filesets: null,
        drug: 'drugs/DRUG1'
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(variantIdSearchResult) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(mockResult) } as any)

    const input = { variant_id: 'NC_000001.11:69633:TGT:GAA', page: 0 }
    const result: any = await variantsDrugsRouters.drugsFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
    expect(result).toHaveLength(1)
    expect(result[0].drug).toBe('drugs/DRUG1')
    expect(result[0].sequence_variant).toBe('variants/NC_000001.11:69633:TGT:GAA')
  })

  it('throws BAD_REQUEST if no variant identifying property is provided', async () => {
    const input = { pmid: '12345', page: 0 } as any
    await expect(
      variantsDrugsRouters.drugsFromVariants({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
