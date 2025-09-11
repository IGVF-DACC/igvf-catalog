import { transcriptsRouters } from '../../../datatypeRouters/nodes/transcripts'
import * as dbModule from '../../../../database'
import * as helpers from '../../../datatypeRouters/_helpers'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')
jest.mock('../../../datatypeRouters/_helpers')

describe('transcriptsRouters.transcripts', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns transcript by transcript_id (human)', async () => {
    const mockRecord = {
      _id: 'T1',
      transcript_type: 'protein_coding',
      chr: 'chr1',
      start: 100,
      end: 200,
      name: 'TX1',
      gene_name: 'GENE1',
      source: 'GENCODE',
      version: 'v1',
      source_url: 'url'
    }
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([mockRecord])
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, transcript_type, chr, start, end, name, gene_name, source, version, source_url')

    const input = { transcript_id: 'T1', page: 0 }
    const result = await transcriptsRouters.transcripts({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockRecord)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('returns transcript by transcript_id (mouse)', async () => {
    const mockRecord = {
      _id: 'MT1',
      transcript_type: 'protein_coding',
      chr: 'chr2',
      start: 300,
      end: 400,
      name: 'MTX1',
      gene_name: 'GENE2',
      source: 'GENCODE',
      version: 'v2',
      source_url: 'url2'
    }
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([mockRecord])
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, transcript_type, chr, start, end, name, gene_name, source, version, source_url')

    const input = { transcript_id: 'MT1', organism: 'Mus musculus', page: 0 }
    const result = await transcriptsRouters.transcripts({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockRecord)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('throws NOT_FOUND if transcript_id not found', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([undefined])
    } as any)
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, transcript_type')

    const input = { transcript_id: 'notfound', page: 0 }
    await expect(
      transcriptsRouters.transcripts({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
