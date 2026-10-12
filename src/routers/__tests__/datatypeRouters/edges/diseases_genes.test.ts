import { diseasesGenesRouters } from '../../../datatypeRouters/edges/diseases_genes'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('diseasesGenesRouters.genesFromDiseases', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns genes associated with a disease_id', async () => {
    const mockResult = [
      {
        disease: 'ontology_terms/DOID_123',
        gene: 'genes/ENSG1',
        name: 'is associated with',
        pmids: ['12345'],
        class: 'observed data',
        method: 'curated',
        label: 'disease-gene association',
        source: 'Orphanet',
        source_url: 'https://example.com',
        association_status: 'Assessed',
        files_filesets: 'files_filesets/FILESET1'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { disease_id: 'DOID_123', page: 0 }
    const result = await diseasesGenesRouters.genesFromDiseases({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('returns genes matched via a disease term_name search', async () => {
    const mockResult = [
      {
        disease: 'ontology_terms/DOID_999',
        gene: 'genes/ENSG2',
        name: 'is associated with',
        class: 'observed data',
        method: 'curated',
        label: 'disease-gene association',
        source: 'GenCC',
        classification: 'Definitive',
        moi_id: 'HP:0000006',
        moi_name: 'Autosomal dominant',
        files_filesets: 'files_filesets/FILESET2'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { disease_name: 'diabetes', page: 0 }
    const result = await diseasesGenesRouters.genesFromDiseases({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST when neither disease_id nor disease_name is provided', async () => {
    const input = { page: 0 } as any
    await expect(
      diseasesGenesRouters.genesFromDiseases({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('diseasesGenesRouters.diseasesFromGenes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns diseases associated with a gene', async () => {
    const geneSearchResult = [
      { _id: 'ENSG1', chr: 'chr1', start: 100, end: 200, gene_type: 'protein_coding', name: 'GENE1', source: 'GENCODE', version: '44', source_url: 'http://x' }
    ]
    const mockResult = [
      {
        disease: 'ontology_terms/DOID_123',
        name: 'is associated with',
        pmids: ['12345'],
        class: 'observed data',
        method: 'curated',
        label: 'disease-gene association',
        source: 'Orphanet',
        source_url: 'https://example.com',
        files_filesets: 'files_filesets/FILESET1'
      }
    ]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(geneSearchResult) } as any)
      .mockResolvedValue({ all: jest.fn().mockResolvedValue(mockResult) } as any)

    const input = { gene_id: 'ENSG1', page: 0 }
    const result = await diseasesGenesRouters.diseasesFromGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('throws BAD_REQUEST when no gene identifying property is provided', async () => {
    const input = { page: 0 } as any
    await expect(
      diseasesGenesRouters.diseasesFromGenes({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
