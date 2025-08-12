import { genesStructureRouters, geneStructureSearch } from '../../datatypeRouters/nodes/genes_structure'
import { db } from '../../../database'
import { TRPCError } from '@trpc/server'
import { appRouter } from '../../_app'

// Mock the database
jest.mock('../../../database', () => ({
  db: {
    query: jest.fn()
  }
}))

// Mock the transcripts_proteins helper
jest.mock('../../datatypeRouters/edges/transcripts_proteins', () => ({
  findTranscriptsFromProteinSearch: jest.fn()
}))

// Mock data constants
const mockGeneStructure = {
  _id: 'ENSG00000139618_ENST00000380152_exon_1',
  name: 'BRCA2',
  chr: '13',
  start: 32315474,
  end: 32400266,
  strand: '+',
  type: 'exon',
  gene_id: 'ENSG00000139618',
  gene_name: 'BRCA2',
  transcript_id: 'ENST00000380152',
  transcript_name: 'BRCA2-201',
  protein_id: 'ENSP00000369497',
  exon_number: '1',
  exon_id: 'ENSE00001484009',
  organism: 'Homo sapiens',
  source: 'Ensembl',
  version: '109',
  source_url: 'https://ensembl.org/Homo_sapiens/Gene/Summary?g=ENSG00000139618'
}

describe('genes_structure router', () => {
  const mockQuery = { all: jest.fn() }

  beforeEach(() => {
    jest.clearAllMocks()
    ;(db.query as jest.Mock).mockReturnValue(mockQuery)
  })

  test('router structure', () => {
    const router = genesStructureRouters.genesStructure
    const openApi = router._def.meta?.openapi

    // Basic router structure
    expect('genesStructure' in genesStructureRouters).toBe(true)
    expect(router._def.query).toBeTruthy()
    expect(openApi?.method).toBe('GET')
    expect(openApi?.path).toBe('/genes-structure')
  })

  test('geneStructureSearch error handling', async () => {
    // Multiple parameter categories should throw error
    await expect(geneStructureSearch({
      gene_id: 'ENSG00000139618',
      transcript_id: 'ENST00000380152',
      page: 0
    })).rejects.toThrow(TRPCError)
    await expect(geneStructureSearch({
      gene_id: 'ENSG00000139618',
      transcript_id: 'ENST00000380152',
      page: 0
    })).rejects.toThrow('Please provide parameters from only one of the four categories: gene, transcript, protein or region')
  })

  test('geneStructureSearch by gene parameters', async () => {
    mockQuery.all.mockResolvedValue([mockGeneStructure])

    // Test gene_id
    const result = await geneStructureSearch({ gene_id: 'ENSG00000139618', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record.gene_id == 'ENSG00000139618'"))
    expect(result).toEqual([mockGeneStructure])

    // Test gene_name
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([mockGeneStructure])
    await geneStructureSearch({ gene_name: 'BRCA2', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record.gene_name == 'BRCA2'"))
  })

  test('geneStructureSearch by transcript parameters', async () => {
    mockQuery.all.mockResolvedValue([mockGeneStructure])

    // Test transcript_id
    const result = await geneStructureSearch({ transcript_id: 'ENST00000380152', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record.transcript_id == 'ENST00000380152'"))
    expect(result).toEqual([mockGeneStructure])

    // Test transcript_name
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([mockGeneStructure])
    await geneStructureSearch({ transcript_name: 'BRCA2-201', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record.transcript_name == 'BRCA2-201'"))
  })

  test('geneStructureSearch by region parameter', async () => {
    mockQuery.all.mockResolvedValue([mockGeneStructure])

    // Test region parameter
    const result = await geneStructureSearch({ region: 'chr13:32315474-32400266', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('OPTIONS { indexHint: "idx_zkd_start_end", forceIndexHint: true }'))
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record.chr == 'chr13'"))
    expect(result).toEqual([mockGeneStructure])
  })

  test('geneStructureSearch by protein parameters', async () => {
    const transcriptsProteinsModule = await import('../../datatypeRouters/edges/transcripts_proteins')
    const findTranscriptsFromProteinSearch = transcriptsProteinsModule.findTranscriptsFromProteinSearch as jest.Mock
    findTranscriptsFromProteinSearch.mockResolvedValue([
      { transcript: 'transcripts/ENST00000380152', protein: 'proteins/ENSP00000369497' }
    ])
    mockQuery.all.mockResolvedValue([mockGeneStructure])

    // Test protein_id
    const result = await geneStructureSearch({ protein_id: 'ENSP00000369497', page: 0 })
    expect(findTranscriptsFromProteinSearch).toHaveBeenCalledWith({
      protein_id: 'ENSP00000369497',
      protein_name: undefined,
      organism: undefined,
      page: 0
    })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('filter record.transcript_id == doc.transcript'))
    expect(result).toEqual([mockGeneStructure])

    // Test protein_name
    jest.clearAllMocks()
    findTranscriptsFromProteinSearch.mockResolvedValue([
      { transcript: 'transcripts/ENST00000380152', protein: 'proteins/ENSP00000369497' }
    ])
    mockQuery.all.mockResolvedValue([mockGeneStructure])
    await geneStructureSearch({ protein_name: 'BRCA2', page: 0 })
    expect(findTranscriptsFromProteinSearch).toHaveBeenCalledWith({
      protein_id: undefined,
      protein_name: 'BRCA2',
      organism: undefined,
      page: 0
    })
  })

  test('geneStructureSearch parameter handling', async () => {
    // Test limit parameter
    mockQuery.all.mockResolvedValue([])
    await geneStructureSearch({ gene_id: 'ENSG00000139618', limit: 10, page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 10'))

    // Test limit capping at MAX_PAGE_SIZE (500)
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([])
    await geneStructureSearch({ gene_id: 'ENSG00000139618', limit: 600, page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 500'))

    // Test page parameter
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([])
    await geneStructureSearch({ gene_id: 'ENSG00000139618', page: 2, limit: 10 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT 20, 10'))

    // Test organism parameter (Mus musculus)
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([])
    await geneStructureSearch({ gene_id: 'ENSMUSG00000041147', organism: 'Mus musculus', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('mm_genes_structure'))
  })

  test('geneStructureSearch with no parameters', async () => {
    mockQuery.all.mockResolvedValue([mockGeneStructure])
    const result = await geneStructureSearch({ page: 0 })
    expect(result).toEqual([mockGeneStructure])
    expect(db.query).not.toHaveBeenCalledWith(expect.stringContaining('FILTER'))
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('SORT record.gene_id, record.transcript_id, record.start'))
  })

  test('tRPC router integration', async () => {
    mockQuery.all.mockResolvedValue([mockGeneStructure])
    const caller = appRouter.createCaller({ requestId: 'test-request-id' })
    const result = await caller.genesStructure({ gene_id: 'ENSG00000139618' })

    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record.gene_id == 'ENSG00000139618'"))
    expect(result).toEqual([mockGeneStructure])
    expect(db.query).toHaveBeenCalledTimes(1)
  })
})
