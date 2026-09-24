import { variantsGenomicElementsGenesRouters } from '../../../datatypeRouters/edges/variants_genomic_elements_genes'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('variantsGenomicElementsGenesRouters.variantsGenomicElementsGenes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns genes near genomic elements overlapping a variant', async () => {
    const variantSearchResult = [
      {
        _id: 'NC_000001.11:69433:A:G',
        chr: 'chr1',
        pos: 69433,
        ref: 'A',
        alt: 'G',
        rsid: ['rs123'],
        spdi: 'NC_000001.11:69433:A:G',
        hgvs: 'NC_000001.11:g.69434A>G',
        ca_id: 'CA123456'
      }
    ]

    const overlappingElements = [
      { _id: 'genomic_elements/GE1', _key: 'GE1', chr: 'chr1', start: 69000, end: 70000, method: 'Perturb-seq' }
    ]

    const mainQueryResult = [
      {
        variant: {
          _id: 'NC_000001.11:69433:A:G',
          chr: 'chr1',
          pos: 69433,
          ref: 'A',
          alt: 'G',
          rsid: ['rs123'],
          spdi: 'NC_000001.11:69433:A:G',
          hgvs: 'NC_000001.11:g.69434A>G',
          ca_id: 'CA123456'
        },
        distance_to_tss: 15000,
        genomic_element: {
          _id: 'GE1',
          name: 'Enhancer1',
          chr: 'chr1',
          start: 69000,
          end: 70000,
          type: 'enhancer',
          source: 'ENCODE',
          source_url: 'http://example.com/ge1'
        },
        gene: {
          _id: 'ENSG1',
          name: 'GENE1',
          chr: 'chr1',
          start: 60000,
          end: 65000,
          strand: '+'
        },
        name: 'regulates',
        label: 'CRISPR screen',
        method: 'Perturb-seq',
        class: 'observed data',
        source: 'IGVF',
        source_url: 'http://example.com/source',
        files_filesets: 'files_filesets/FILESET1',
        biological_context: 'ontology_terms/CL_0000000',
        biosample_term: 'ontology_terms/CL_0000000',
        crispr_modality: 'CRISPRi',
        log2FC: -1.2,
        neg_log10_pvalue: 5.5,
        neg_log10_pvalue_adj: 4.2,
        p_value: 0.0001,
        p_value_adj: 0.001,
        effect_size: -0.5,
        significant: true
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(variantSearchResult) } as any) // variantSearch
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(overlappingElements) } as any) // overlappingElementsQuery
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mainQueryResult) } as any) // main query

    const input = { variant_id: 'NC_000001.11:69433:A:G', page: 0 }
    const result = await variantsGenomicElementsGenesRouters.variantsGenomicElementsGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mainQueryResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(3)
  })

  it('returns an empty array when no overlapping Perturb-seq elements are found', async () => {
    const variantSearchResult = [
      {
        _id: 'NC_000001.11:69433:A:G',
        chr: 'chr1',
        pos: 69433,
        ref: 'A',
        alt: 'G',
        rsid: ['rs123'],
        spdi: 'NC_000001.11:69433:A:G',
        hgvs: 'NC_000001.11:g.69434A>G',
        ca_id: 'CA123456'
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(variantSearchResult) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([{ chr: 'chr1', start: 69000, end: 70000, method: 'ChIP-seq' }]) } as any)

    const input = { variant_id: 'NC_000001.11:69433:A:G', page: 0 }
    const result = await variantsGenomicElementsGenesRouters.variantsGenomicElementsGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual([])
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('throws NOT_FOUND when the variant does not exist', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)

    const input = { variant_id: 'NC_000099.11:1:A:G', page: 0 }
    await expect(
      variantsGenomicElementsGenesRouters.variantsGenomicElementsGenes({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST when no variant identifying property is provided', async () => {
    const input = { page: 0 } as any
    await expect(
      variantsGenomicElementsGenesRouters.variantsGenomicElementsGenes({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
