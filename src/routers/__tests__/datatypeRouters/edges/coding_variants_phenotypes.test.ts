import { codingVariantsPhenotypesRouters } from '../../../datatypeRouters/edges/coding_variants_phenotypes'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('codingVariantsPhenotypesRouters.codingVariantsFromPhenotypes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns coding variants for a phenotype_id', async () => {
    const mockResult = [
      {
        coding_variant: {
          _id: 'CV1',
          aapos: 203,
          hgvsp: 'p.Cys203Glu',
          protein_name: 'A0A2U3U0J3_HUMAN',
          gene_name: 'BRCA1',
          ref: 'C',
          alt: 'E'
        },
        phenotype: {
          phenotype_id: 'PHENOTYPE1',
          phenotype_name: 'breast cancer'
        },
        variant: {
          chr: 'chr1',
          pos: 69633,
          ref: 'TGT',
          alt: 'GAA',
          rsid: null,
          spdi: 'NC_000001.11:69633:TGT:GAA',
          hgvs: 'NC_000001.11:g.69634_69636delinsGAA',
          ca_id: null,
          _id: 'NC_000001.11:69633:TGT:GAA'
        },
        score: 1.2,
        method: 'SGE',
        class: 'observed data',
        label: 'functional score',
        source: 'MaveDB',
        source_url: 'http://example.com/sge_score',
        files_filesets: 'files_filesets/FILESET1'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { phenotype_id: 'PHENOTYPE1', page: 0 }
    const result = await codingVariantsPhenotypesRouters.codingVariantsFromPhenotypes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('resolves phenotype_name to an exact ontology match before running the main query', async () => {
    const mockResult = [
      {
        coding_variant: {
          _id: 'CV2',
          aapos: 45,
          hgvsp: 'p.Val45Ile',
          protein_name: 'PROT1_HUMAN',
          gene_name: 'TP53',
          ref: 'V',
          alt: 'I'
        },
        phenotype: {
          phenotype_id: 'PHENOTYPE2',
          phenotype_name: 'lung cancer'
        },
        variant: null,
        score: 0.4,
        method: 'ESM-1v',
        class: 'observed data',
        label: null,
        source: 'ESM-1v',
        source_url: 'http://example.com/esm1v',
        files_filesets: null
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(['ontology_terms/PHENOTYPE2']) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(mockResult) } as any)

    const input = { phenotype_name: 'lung cancer', page: 0 }
    const result = await codingVariantsPhenotypesRouters.codingVariantsFromPhenotypes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('throws BAD_REQUEST if no identifying property is provided', async () => {
    const input = { page: 0 } as any
    await expect(
      codingVariantsPhenotypesRouters.codingVariantsFromPhenotypes({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST if method is invalid', async () => {
    const input = { method: 'NOT_A_METHOD', page: 0 } as any
    await expect(
      codingVariantsPhenotypesRouters.codingVariantsFromPhenotypes({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('codingVariantsPhenotypesRouters.phenotypesFromCodingVariants', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns phenotypes for a coding_variant_name', async () => {
    const mockResult = [
      {
        coding_variant: {
          _id: 'CV1',
          aapos: 203,
          hgvsp: 'p.Cys203Glu',
          protein_name: 'A0A2U3U0J3_HUMAN',
          gene_name: 'BRCA1',
          ref: 'C',
          alt: 'E'
        },
        variant: {
          chr: 'chr1',
          pos: 69633,
          ref: 'TGT',
          alt: 'GAA',
          rsid: null,
          spdi: 'NC_000001.11:69633:TGT:GAA',
          hgvs: 'NC_000001.11:g.69634_69636delinsGAA',
          ca_id: null,
          _id: 'NC_000001.11:69633:TGT:GAA'
        },
        phenotype: {
          phenotype_id: 'PHENOTYPE1',
          phenotype_name: 'breast cancer'
        },
        source: 'MaveDB',
        method: 'SGE',
        class: 'observed data',
        label: 'functional score',
        files_filesets: 'files_filesets/FILESET1',
        score: 1.2,
        source_url: 'http://example.com/sge_score'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { coding_variant_name: 'CV1', page: 0 }
    const result = await codingVariantsPhenotypesRouters.phenotypesFromCodingVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST if no coding-variant identifying property is provided', async () => {
    const input = { page: 0 } as any
    await expect(
      codingVariantsPhenotypesRouters.phenotypesFromCodingVariants({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('codingVariantsPhenotypesRouters.codingVariantsCountFromGene', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns cached counts when present and only makes one query', async () => {
    const cachedResult = [
      { method: 'SGE', count: 12 },
      { method: 'VAMP-seq', count: 3 }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([cachedResult]) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue([]) } as any)

    const input = { gene_id: 'GENE1' }
    const result = await codingVariantsPhenotypesRouters.codingVariantsCountFromGene({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(cachedResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('falls back to the main query when no cached counts are found', async () => {
    const mockResult = [{ method: 'SGE', count: 5 }]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(mockResult) } as any)

    const input = { gene_id: 'GENE2' }
    const result = await codingVariantsPhenotypesRouters.codingVariantsCountFromGene({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('skips the cache entirely when files_fileset is provided', async () => {
    const mockResult = [{ method: 'SGE', count: 2 }]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { gene_id: 'GENE3', files_fileset: 'FILESET1' }
    const result = await codingVariantsPhenotypesRouters.codingVariantsCountFromGene({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST if gene_id is missing', async () => {
    const input = {} as any
    await expect(
      codingVariantsPhenotypesRouters.codingVariantsCountFromGene({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('codingVariantsPhenotypesRouters.codingVariantsSummary', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns score summaries for a coding_variant_id', async () => {
    const mockResult = [
      {
        variant_id: 'variants/NC_000001.11:69633:TGT:GAA',
        hgvsp: 'p.Cys203Glu',
        gene_name: 'BRCA1',
        transcript_id: 'ENST00000641515',
        dataType: 'SGE',
        score: 1.2,
        portalLink: 'http://example.com/sge_score'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { coding_variant_id: 'CV1' }
    const result = await codingVariantsPhenotypesRouters.codingVariantsSummary({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST if neither variant_id nor coding_variant_id is provided', async () => {
    const input = {} as any
    await expect(
      codingVariantsPhenotypesRouters.codingVariantsSummary({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('codingVariantsPhenotypesRouters.deprecatedCodingVariantsSummary', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns score summaries for a variant_id', async () => {
    const mockResult = [
      {
        variant_id: 'variants/NC_000001.11:69633:TGT:GAA',
        hgvsp: 'p.Cys203Glu',
        gene_name: 'BRCA1',
        transcript_id: 'ENST00000641515',
        dataType: 'VAMP-seq',
        score: 0.8,
        portalLink: 'http://example.com/vamp_seq_score'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { variant_id: 'NC_000001.11:69633:TGT:GAA' }
    const result = await codingVariantsPhenotypesRouters.deprecatedCodingVariantsSummary({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST if neither variant_id nor coding_variant_id is provided', async () => {
    const input = {} as any
    await expect(
      codingVariantsPhenotypesRouters.deprecatedCodingVariantsSummary({
        input, ctx: {}, type: 'query', path: '', rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
