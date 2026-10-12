import { genesTranscriptsRouters } from '../../../datatypeRouters/edges/genes_transcripts'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('genesTranscriptsRouters.transcriptsFromGenes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns transcripts for a gene search', async () => {
    const geneSearchResult = [{ _id: 'ENSG00000012048', name: 'BRCA1' }]
    const mockResult = [{
      gene: 'genes/ENSG00000012048',
      transcript: 'transcripts/ENST00000357654',
      source: 'GENCODE',
      source_url: 'https://www.gencodegenes.org',
      version: '44',
      name: 'is transcribed as'
    }]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(geneSearchResult) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mockResult) } as any)

    const input = { gene_id: 'ENSG00000012048', page: 0 }
    const result = await genesTranscriptsRouters.transcriptsFromGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('throws BAD_REQUEST if no gene property is defined', async () => {
    const input = { page: 0 }
    await expect(
      genesTranscriptsRouters.transcriptsFromGenes({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('genesTranscriptsRouters.genesFromTranscripts', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns genes for a transcript identified by transcript_id', async () => {
    const mockResult = [{
      transcript: 'transcripts/ENST00000357654',
      gene: 'genes/ENSG00000012048',
      source: 'GENCODE',
      source_url: 'https://www.gencodegenes.org',
      version: '44',
      name: 'is transcript of'
    }]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { transcript_id: 'ENST00000357654', page: 0 }
    const result = await genesTranscriptsRouters.genesFromTranscripts({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('returns genes for transcripts within a region', async () => {
    const mockResult = [{
      transcript: 'transcripts/ENST00000357654',
      gene: 'genes/ENSG00000012048',
      source: 'GENCODE',
      source_url: 'https://www.gencodegenes.org',
      version: '44',
      name: 'is transcript of'
    }]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { region: 'chr17:43044000-43045000', page: 0 }
    const result = await genesTranscriptsRouters.genesFromTranscripts({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST if no query parameter is defined', async () => {
    const input = { page: 0 }
    await expect(
      genesTranscriptsRouters.genesFromTranscripts({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('genesTranscriptsRouters.proteinsFromGenes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns proteins for a gene search', async () => {
    const geneSearchResult = [{ _id: 'ENSG00000012048', name: 'BRCA1' }]
    const mockResult = [{
      gene: 'genes/ENSG00000012048',
      protein: 'proteins/ENSP00000493376'
    }]

    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(geneSearchResult) } as any)
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mockResult) } as any)

    const input = { gene_name: 'BRCA1', page: 0 }
    const result = await genesTranscriptsRouters.proteinsFromGenes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(2)
  })

  it('throws BAD_REQUEST if no gene property is defined', async () => {
    const input = { page: 0 }
    await expect(
      genesTranscriptsRouters.proteinsFromGenes({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('genesTranscriptsRouters.genesFromProteins', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns genes for a protein identified by protein_id', async () => {
    const mockResult = [{
      protein: 'proteins/ENSP00000493376',
      gene: 'genes/ENSG00000012048'
    }]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { protein_id: 'ENSP00000493376', page: 0 }
    const result = await genesTranscriptsRouters.genesFromProteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('returns genes for a protein search by protein_name', async () => {
    const mockResult = [{
      protein: 'proteins/ENSP00000493376',
      gene: 'genes/ENSG00000012048'
    }]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { protein_name: 'BRCA1_HUMAN', page: 0 }
    const result = await genesTranscriptsRouters.genesFromProteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })
})
