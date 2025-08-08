import { genesRouters, findGenesByTextSearch, nearestGeneSearch } from '../../../datatypeRouters/nodes/genes'
import * as dbModule from '../../../../database'
import * as helpers from '../../../datatypeRouters/_helpers'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../database')
jest.mock('../../../datatypeRouters/_helpers')

describe('genesRouters.genes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns genes by gene_id', async () => {
    const mockResult = [{ _id: '1', name: 'GeneA', chr: 'chr1', source: 'src', source_url: 'url', version: 'v1', start: null, end: null, gene_type: null, strand: null, hgnc: null, entrez: null, collections: null, study_sets: null }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'preProcessRegionParam').mockImplementation((input: any) => input)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('_key == "1"')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name, chr, source, source_url')

    const input = { gene_id: '1', page: 0 }
    const result = await genesRouters.genes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
    expect(dbModule.db.query).toHaveBeenCalled()
  })

  it('returns genes by text search if no results from main query', async () => {
    const mockResult = [{ _id: '2', name: 'GeneB', chr: 'chr1', source: 'src', source_url: 'url', version: 'v1', start: null, end: null, gene_type: null, strand: null, hgnc: null, entrez: null, collections: null, study_sets: null }]
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any) // main query returns []
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mockResult) } as any) // text search returns result
    jest.spyOn(helpers, 'preProcessRegionParam').mockImplementation((input: any) => input)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name')

    const input = { name: 'GeneB', page: 0 }
    const result = await genesRouters.genes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
  })

  it('returns empty array if no results found', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([])
    } as any)
    jest.spyOn(helpers, 'preProcessRegionParam').mockImplementation((input: any) => input)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name')

    const input = { page: 0 }
    const result = await genesRouters.genes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual([])
  })

  it('formats hgnc and entrez ids', async () => {
    const mockResult = [{ _id: '3', name: 'GeneC', chr: 'chr1', source: 'src', source_url: 'url', version: 'v1', start: null, end: null, gene_type: null, strand: null, hgnc: null, entrez: null, collections: null, study_sets: null }]
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue(mockResult)
    } as any)
    jest.spyOn(helpers, 'preProcessRegionParam').mockImplementation((input: any) => input)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name')

    const input = { hgnc_id: '1234', entrez: '5678', page: 0 }
    const result = await genesRouters.genes({
      input,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: input
    })
    expect(result).toEqual(mockResult)
  })

  it('throws BAD_REQUEST for invalid region in nearestGeneSearch', async () => {
    jest.spyOn(helpers, 'validRegion').mockReturnValue(null)
    await expect(
      nearestGeneSearch({ region: 'invalid' })
    ).rejects.toThrow(TRPCError)
  })

  it('returns nearest genes if region is valid', async () => {
    const mockResult = [{ _id: '4', name: 'GeneD', chr: 'chr1', source: 'src', source_url: 'url', version: 'v1', start: null, end: null, gene_type: null, strand: null, hgnc: null, entrez: null, collections: null, study_sets: null }]
    jest.spyOn(helpers, 'validRegion').mockReturnValue(['region', 'chr1', '100', '200'])
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name')
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any) // inRegionQuery returns []
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([mockResult]) } as any) // nearestQuery returns [[{...}]]

    const input = { region: 'chr1:100-200', page: 0 }
    const result = await nearestGeneSearch(input)
    expect(result).toEqual(mockResult)
  })

  it('findGenesByTextSearch returns fuzzy results if no token results', async () => {
    const mockResult = [{ _id: '5', name: 'GeneE', chr: 'chr1', source: 'src', source_url: 'url', version: 'v1', start: null, end: null, gene_type: null, strand: null, hgnc: null, entrez: null, collections: null, study_sets: null }]
    const geneSchema = { db_collection_name: 'genes' }
    jest.spyOn(helpers, 'preProcessRegionParam').mockImplementation((input: any) => input)
    jest.spyOn(helpers, 'getFilterStatements').mockReturnValue('')
    jest.spyOn(helpers, 'getDBReturnStatements').mockReturnValue('_id, name')
    jest.spyOn(dbModule.db, 'query')
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue([]) } as any) // token search returns []
      .mockResolvedValueOnce({ all: jest.fn().mockResolvedValue(mockResult) } as any) // fuzzy search returns result

    const input = { name: 'GeneE', page: 0 }
    const result = await findGenesByTextSearch(input, geneSchema as any)
    expect(result).toEqual(mockResult)
  })
})
