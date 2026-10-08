import { variantsDiseasesRouters } from '../../../datatypeRouters/edges/variants_diseases'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('variantsDiseasesRouters.variantsFromDiseases', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns variants associated with a disease_id', async () => {
    const mockResult = [
      {
        sequence_variant: 'variants/NC_000005.10:1779518:G:A',
        disease: 'ontology_terms/MONDO_0009861',
        gene_name: 'CFTR',
        assertion: 'Pathogenic',
        pmids: ['http://pubmed.ncbi.nlm.nih.gov/2574002'],
        class: 'observed data',
        method: null,
        label: null,
        files_filesets: 'files_filesets/IGVFFI5852GYTT',
        source: 'ClinGen',
        source_url: 'https://search.clinicalgenome.org/kb/downloads',
        name: 'associated with'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { disease_id: 'MONDO_0009861', page: 0 }
    const result = await variantsDiseasesRouters.variantsFromDiseases({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('returns variants associated with a disease found by disease_name', async () => {
    const mockResult = [
      {
        sequence_variant: 'variants/NC_000005.10:1779518:G:A',
        disease: 'ontology_terms/MONDO_0009861',
        gene_name: 'CFTR',
        assertion: 'Likely Pathogenic',
        pmids: ['http://pubmed.ncbi.nlm.nih.gov/9450897'],
        class: 'observed data',
        method: null,
        label: null,
        files_filesets: 'files_filesets/IGVFFI5852GYTT',
        source: 'ClinGen',
        source_url: 'https://search.clinicalgenome.org/kb/downloads',
        name: 'associated with'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { disease_name: 'cystic fibrosis', page: 0 }
    const result = await variantsDiseasesRouters.variantsFromDiseases({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST when neither disease_id nor disease_name is defined', async () => {
    const input = { page: 0 } as any
    await expect(
      variantsDiseasesRouters.variantsFromDiseases({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('variantsDiseasesRouters.diseaseFromVariants', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('resolves the variant ID first, then queries diseases (two sequential db calls)', async () => {
    const variantIDs = ['variants/NC_000005.10:1779518:G:A']
    const mockResult = [
      {
        sequence_variant: 'variants/NC_000005.10:1779518:G:A',
        disease: 'ontology_terms/MONDO_0009861',
        gene_name: 'CFTR',
        assertion: 'Pathogenic',
        pmids: ['http://pubmed.ncbi.nlm.nih.gov/2574002'],
        class: 'observed data',
        method: null,
        label: null,
        files_filesets: 'files_filesets/IGVFFI5852GYTT',
        source: 'ClinGen',
        source_url: 'https://search.clinicalgenome.org/kb/downloads',
        name: 'associated with'
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(variantIDs) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(mockResult) } as any)

    const input = { variant_id: 'NC_000005.10:1779518:G:A', page: 0 }
    const result = await variantsDiseasesRouters.diseaseFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('filters by pmid and assertion in addition to the variant identifier', async () => {
    const variantIDs = ['variants/NC_000005.10:1779518:G:A']
    const mockResult = [
      {
        sequence_variant: 'variants/NC_000005.10:1779518:G:A',
        disease: 'ontology_terms/MONDO_0009861',
        gene_name: 'CFTR',
        assertion: 'Pathogenic',
        pmids: ['http://pubmed.ncbi.nlm.nih.gov/2574002'],
        class: 'observed data',
        method: null,
        label: null,
        files_filesets: 'files_filesets/IGVFFI5852GYTT',
        source: 'ClinGen',
        source_url: 'https://search.clinicalgenome.org/kb/downloads',
        name: 'associated with'
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(variantIDs) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(mockResult) } as any)

    const input = { variant_id: 'NC_000005.10:1779518:G:A', pmid: '2574002', assertion: 'Pathogenic', page: 0 }
    const result = await variantsDiseasesRouters.diseaseFromVariants({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('throws BAD_REQUEST when no variant identifying property is defined', async () => {
    const input = { page: 0 } as any
    await expect(
      variantsDiseasesRouters.diseaseFromVariants({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
