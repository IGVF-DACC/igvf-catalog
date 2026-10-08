import { transcriptsProteinsRouters } from '../../../datatypeRouters/edges/transcripts_proteins'
import * as dbModule from '../../../../database'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')

describe('transcriptsProteinsRouters.proteinsFromTranscripts', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns proteins encoded by a transcript_id', async () => {
    const mockResult = [
      {
        source: 'GENCODE',
        source_url: 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz',
        protein: 'proteins/ENSP00000493376',
        transcript: 'transcripts/ENST00000641515',
        name: 'translates to'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { transcript_id: 'ENST00000641515', page: 0 }
    const result = await transcriptsProteinsRouters.proteinsFromTranscripts({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('returns proteins encoded by transcripts located in a region', async () => {
    const mockResult = [
      {
        source: 'GENCODE',
        source_url: 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz',
        protein: 'proteins/ENSP00000493376',
        transcript: 'transcripts/ENST00000641515',
        name: 'translates to'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { region: 'chr1:65565-65573', page: 0 }
    const result = await transcriptsProteinsRouters.proteinsFromTranscripts({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('throws BAD_REQUEST when no transcript parameter is defined', async () => {
    const input = { page: 0 } as any
    await expect(
      transcriptsProteinsRouters.proteinsFromTranscripts({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})

describe('transcriptsProteinsRouters.transcriptsFromProteins', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns transcripts encoding a protein looked up by protein_id', async () => {
    const mockResult = [
      {
        protein: 'proteins/ENSP00000493376',
        transcript: 'transcripts/ENST00000641515',
        source: 'GENCODE',
        source_url: 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz',
        name: 'translated from'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { protein_id: 'ENSP00000493376', page: 0 }
    const result = await transcriptsProteinsRouters.transcriptsFromProteins({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })

    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalledTimes(1)
  })

  it('returns transcripts encoding a protein looked up by protein_name', async () => {
    const mockResult = [
      {
        protein: 'proteins/ENSP00000493376',
        transcript: 'transcripts/ENST00000641515',
        source: 'GENCODE',
        source_url: 'https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.chr_patch_hapl_scaff.annotation.gtf.gz',
        name: 'translated from'
      }
    ]

    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)

    const input = { protein_name: 'A0A2U3U0J3_HUMAN', page: 0 }
    const result = await transcriptsProteinsRouters.transcriptsFromProteins({
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
