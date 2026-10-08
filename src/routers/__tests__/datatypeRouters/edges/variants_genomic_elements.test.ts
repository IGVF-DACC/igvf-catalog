import { variantsGenomicElementsRouters } from '../../../datatypeRouters/edges/variants_genomic_elements'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('variantsGenomicElementsRouters.predictionsFromVariants', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns cell/gene predictions for a variant', async () => {
    const mockResult = [{
      distance_gene_variant: 1000,
      element_chr: 'chr1',
      element_start: 69000,
      element_end: 70000,
      element_type: 'candidate cis regulatory element',
      id: 'genomic_elements/GE1',
      cell_type: 'K562',
      target_gene: { gene_name: 'BRCA1', id: 'genes/ENSG00000012048', chr: 'chr1', start: 68000, end: 71000 },
      score: 0.87,
      model: 'scE2G',
      dataset: 'https://example.com/dataset',
      name: 'GE1_BRCA1',
      method: 'scE2G',
      files_filesets: 'files_filesets/IGVFFI0001XXXX'
    }]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { spdi: 'NC_000001.11:69634:A:G', page: 0 }
    const result = await variantsGenomicElementsRouters.predictionsFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST when no variant identifying property is defined', async () => {
    const input = {}
    await expect(
      variantsGenomicElementsRouters.predictionsFromVariants({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('variantsGenomicElementsRouters.genomicElementsFromVariantsCount', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns aggregated cell types, genes and methods for a variant', async () => {
    const variantSearchResult = [{ _id: 'V1', chr: 'chr1', pos: 69634, ref: 'A', alt: 'G' }]
    const genomicElementsResult = [{ id: 'genomic_elements/GE1', chr: 'chr1', start: 69000, end: 70000, type: 'candidate cis regulatory element' }]
    const finalResult = [{
      cell_types: ['K562'],
      genes: [{ gene_name: 'BRCA1', id: 'genes/ENSG00000012048' }],
      methods: [{ method: 'scE2G', count: 3 }],
      name: 'regulates'
    }]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(variantSearchResult) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(genomicElementsResult) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(finalResult) } as any)

    const input = { spdi: 'NC_000001.11:69634:A:G' }
    const result = await variantsGenomicElementsRouters.genomicElementsFromVariantsCount({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(finalResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(3)
  })

  it('throws NOT_FOUND when the variant does not exist', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValueOnce({
      all: jest.fn().mockResolvedValue([])
    } as any)

    const input = { spdi: 'NC_000001.11:00000:A:G' }
    await expect(
      variantsGenomicElementsRouters.genomicElementsFromVariantsCount({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST when no variant property is defined', async () => {
    const input = {}
    await expect(
      variantsGenomicElementsRouters.genomicElementsFromVariantsCount({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('variantsGenomicElementsRouters.genomicElementsPredictionsFromVariant', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns cell types and genes predicted for a variant', async () => {
    const mockResult = [{
      'sequence variant': {
        _id: 'V1',
        chr: 'chr1',
        pos: 69634,
        rsid: ['rs123'],
        ref: 'A',
        alt: 'G',
        spdi: 'NC_000001.11:69634:A:G',
        hgvs: 'NC_000001.11:g.69634A>G',
        ca_id: 'CA123'
      },
      predictions: {
        cell_types: ['K562', 'HepG2'],
        genes: [{ gene_name: 'BRCA1', id: 'genes/ENSG00000012048' }]
      }
    }]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { spdi: 'NC_000001.11:69634:A:G' }
    const result = await variantsGenomicElementsRouters.genomicElementsPredictionsFromVariant({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult[0])
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws NOT_FOUND when the variant does not exist', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)

    const input = { spdi: 'NC_000001.11:00000:A:G' }
    await expect(
      variantsGenomicElementsRouters.genomicElementsPredictionsFromVariant({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST when no parameter is defined', async () => {
    const input = {}
    await expect(
      variantsGenomicElementsRouters.genomicElementsPredictionsFromVariant({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('variantsGenomicElementsRouters.variantsFromGenomicElements', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns variants intersecting genomic elements filtered by method', async () => {
    const mockResult = [{
      variant: {
        chr: 'chr1',
        pos: 69634,
        ref: 'A',
        alt: 'G',
        rsid: ['rs123'],
        spdi: 'NC_000001.11:69634:A:G',
        hgvs: 'NC_000001.11:g.69634A>G',
        ca_id: 'CA123',
        _id: 'variants/V1'
      },
      name: 'modulates accessibility of',
      label: 'variant-element',
      method: 'caQTL',
      class: 'observed data',
      log2FC: 0.5,
      neg_log10_pvalue: 3.2,
      beta: null,
      files_filesets: 'files_filesets/IGVFFI0001XXXX',
      biological_context: 'lymphoblastoid cell line',
      biosample_term: 'ontology_terms/EFO_0005292',
      source: 'AFGR',
      source_url: 'https://github.com/smontgomlab/AFGR',
      genomic_element: {
        _id: 'genomic_elements/GE1',
        name: 'GE1',
        chr: 'chr1',
        start: 69000,
        end: 70000,
        type: 'candidate cis regulatory element',
        source_annotation: null,
        source: 'ENCODE',
        source_url: 'https://www.encodeproject.org'
      }
    }]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { method: 'caQTL', page: 0 }
    const result = await variantsGenomicElementsRouters.variantsFromGenomicElements({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST when no region, method or files_fileset is defined', async () => {
    const input = { page: 0 }
    await expect(
      variantsGenomicElementsRouters.variantsFromGenomicElements({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('variantsGenomicElementsRouters.genomicElementsFromVariants', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns genomic elements intersecting variants filtered by method', async () => {
    const mockResult = [{
      variant: {
        chr: 'chr1',
        pos: 69634,
        ref: 'A',
        alt: 'G',
        rsid: ['rs123'],
        spdi: 'NC_000001.11:69634:A:G',
        hgvs: 'NC_000001.11:g.69634A>G',
        ca_id: 'CA123',
        _id: 'variants/V1'
      },
      name: 'modulates accessibility of',
      label: 'variant-element',
      method: 'caQTL',
      class: 'observed data',
      log2FC: 0.5,
      neg_log10_pvalue: 3.2,
      beta: null,
      files_filesets: 'files_filesets/IGVFFI0001XXXX',
      biological_context: 'lymphoblastoid cell line',
      biosample_term: 'ontology_terms/EFO_0005292',
      source: 'AFGR',
      source_url: 'https://github.com/smontgomlab/AFGR',
      genomic_element: {
        _id: 'genomic_elements/GE1',
        name: 'GE1',
        chr: 'chr1',
        start: 69000,
        end: 70000,
        type: 'candidate cis regulatory element',
        source_annotation: null,
        source: 'ENCODE',
        source_url: 'https://www.encodeproject.org'
      }
    }]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { method: 'caQTL', page: 0 }
    const result = await variantsGenomicElementsRouters.genomicElementsFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST when no variant property, method or files_fileset is defined', async () => {
    const input = { page: 0 }
    await expect(
      variantsGenomicElementsRouters.genomicElementsFromVariants({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('variantsGenomicElementsRouters.variantsRegionSummary', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns a variant count and method breakdown for a region', async () => {
    const mockResult = [{
      variant_count: 5,
      by_method: [{ method: 'eQTL', count: 3 }, { method: 'caQTL', count: 2 }]
    }]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { region: 'chr1:1000-2000' }
    const result = await variantsGenomicElementsRouters.variantsRegionSummary({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult[0])
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST when the region span exceeds 10kb', async () => {
    const input = { region: 'chr1:1000-20000' }
    await expect(
      variantsGenomicElementsRouters.variantsRegionSummary({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST when region is missing', async () => {
    const input = {} as any
    await expect(
      variantsGenomicElementsRouters.variantsRegionSummary({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
