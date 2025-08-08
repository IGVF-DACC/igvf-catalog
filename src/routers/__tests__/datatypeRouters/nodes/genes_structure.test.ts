import { genesStructureRouters } from '../../../datatypeRouters/nodes/genes_structure'
import * as dbModule from '../../../../database'
import * as helpers from '../../../datatypeRouters/_helpers'
import * as proteinModule from '../../../datatypeRouters/edges/transcripts_proteins'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')
jest.mock('../../../datatypeRouters/_helpers')
jest.mock('../../../datatypeRouters/edges/transcripts_proteins')

describe('genesStructureRouters.genesStructure', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns gene structure by gene_id', async () => {
    const mockResult = [{
      _id: '1',
      name: 'Gene1',
      chr: 'chr1',
      start: 100,
      end: 200,
      strand: '+',
      type: 'protein_coding',
      gene_id: 'GENE1',
      gene_name: 'Gene1',
      transcript_id: 'T1',
      transcript_name: 'T1',
      exon_number: '1',
      exon_id: null,
      organism: 'Homo sapiens',
      source: 'GENCODE',
      version: 'v43',
      source_url: 'https://www.gencodegenes.org/human/'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'preProcessRegionParam').mockImplementation(input => input)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('gene_id == "GENE1"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, gene_id, transcript_id, start, end')

    const input = { gene_id: 'GENE1', page: 0 }
    const result = await genesStructureRouters.genesStructure({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('returns gene structure by region', async () => {
    const mockResult = [{
      _id: '2',
      name: 'Gene2',
      chr: 'chr2',
      start: 100,
      end: 200,
      strand: '+',
      type: 'protein_coding',
      gene_id: 'GENE2',
      gene_name: 'Gene2',
      transcript_id: 'T2',
      transcript_name: 'T2',
      exon_number: '2',
      exon_id: null,
      organism: 'Homo sapiens',
      source: 'GENCODE',
      version: 'v43',
      source_url: 'https://www.gencodegenes.org/human/'
    }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'preProcessRegionParam').mockImplementation(input => input)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('region == "chr1:100-200"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, gene_id, transcript_id, start, end')

    const input = { region: 'chr1:100-200', page: 0 }
    const result = await genesStructureRouters.genesStructure({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('returns gene structure by protein_id', async () => {
    const proteinTranscripts = [
      { transcript: 'transcripts/TX1', protein: 'proteins/PX1' }
    ]
    const mockResult = [{
      _id: '3',
      name: 'Gene3',
      chr: 'chr3',
      start: 100,
      end: 200,
      strand: '+',
      type: 'protein_coding',
      gene_id: 'GENE3',
      gene_name: 'Gene3',
      transcript_id: 'T3',
      transcript_name: 'T3',
      exon_number: '3',
      exon_id: null,
      organism: 'Homo sapiens',
      source: 'GENCODE',
      version: 'v43',
      source_url: 'https://www.gencodegenes.org/human/'
    }]
    jest.spyOn(proteinModule, 'findTranscriptsFromProteinSearch').mockResolvedValue(proteinTranscripts)
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'preProcessRegionParam').mockImplementation(input => input)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, gene_id, transcript_id, protein_id, start, end')

    const input = { protein_id: 'PX1', page: 0 }
    const result = await genesStructureRouters.genesStructure({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
    expect(proteinModule.findTranscriptsFromProteinSearch).toHaveBeenCalled()
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('throws BAD_REQUEST if multiple parameter categories are provided', async () => {
    const input = { gene_id: 'GENE1', transcript_id: 'TX1', page: 0 }
    await expect(
      genesStructureRouters.genesStructure({
        input,
        ctx: {},
        type: 'query',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
