import { genomicRegionsRouters, genomicElementSearch } from '../../datatypeRouters/nodes/genomic_elements'
import { db } from '../../../database'
import { appRouter } from '../../_app'

// Mock the database
jest.mock('../../../database', () => ({
  db: {
    query: jest.fn()
  }
}))

// Mock data constants
const mockGenomicElement = {
  _id: 'ENCSR831INH',
  chr: 'chr1',
  start: 1157527,
  end: 1158185,
  name: 'ABC123',
  source_annotation: 'enhancer',
  type: 'candidate_cis_regulatory_element',
  source: 'ENCODE_EpiRaction',
  source_url: 'https://www.encodeproject.org/annotations/ENCSR831INH/'
}

describe('genomic elements router', () => {
  const mockQuery = { all: jest.fn() }

  beforeEach(() => {
    jest.clearAllMocks()
    ;(db.query as jest.Mock).mockReturnValue(mockQuery)
  })

  test('router structure', () => {
    const router = genomicRegionsRouters.genomicElements
    const openApi = router._def.meta?.openapi

    // Basic router structure
    expect('genomicElements' in genomicRegionsRouters).toBe(true)
    expect(router._def.query).toBeTruthy()
    expect(openApi?.method).toBe('GET')
    expect(openApi?.path).toBe('/genomic-elements')
  })

  test('genomicElementSearch by various parameters', async () => {
    mockQuery.all.mockResolvedValue([mockGenomicElement])

    // Test region parameter
    const result = await genomicElementSearch({ region: 'chr1:1157527-1158185', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('OPTIONS { indexHint: "idx_zkd_start_end", forceIndexHint: true }'))
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('FILTER record.chr == \'chr1\' and record.start < 1158185 AND record.end > 1157527'))
    expect(result).toEqual([mockGenomicElement])

    // Test source_annotation parameter
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([mockGenomicElement])
    await genomicElementSearch({ source_annotation: 'enhancer', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('FILTER record.source_annotation == \'enhancer\''))

    // Test type parameter
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([mockGenomicElement])
    await genomicElementSearch({ type: 'candidate_cis_regulatory_element', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('FILTER record.type == \'candidate_cis_regulatory_element\''))

    // Test source parameter
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([mockGenomicElement])
    await genomicElementSearch({ source: 'ENCODE_EpiRaction', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('FILTER record.source == \'ENCODE_EpiRaction\''))
  })

  test('genomicElementSearch by organism', async () => {
    mockQuery.all.mockResolvedValue([mockGenomicElement])

    // Test human organism (default)
    await genomicElementSearch({ organism: 'Homo sapiens', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('genomic_elements'))

    // Test mouse organism
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([mockGenomicElement])
    await genomicElementSearch({ organism: 'Mus musculus', page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('mm_genomic_elements'))
  })

  test('genomicElementSearch parameter handling', async () => {
    // Test limit parameter
    mockQuery.all.mockResolvedValue([])
    await genomicElementSearch({ limit: 50, page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 50'))

    // Test limit capping
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([])
    await genomicElementSearch({ limit: 1500, page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 1000'))

    // Test multiple parameters
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([mockGenomicElement])
    const result = await genomicElementSearch({
      region: 'chr1:1157527-1158185',
      source_annotation: 'enhancer',
      page: 0
    })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('OPTIONS { indexHint: "idx_zkd_start_end", forceIndexHint: true }'))
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('FILTER record.source_annotation == \'enhancer\' and record.chr == \'chr1\' and record.start < 1158185 AND record.end > 1157527'))
    expect(result).toEqual([mockGenomicElement])
  })

  test('genomicElementSearch with empty results', async () => {
    mockQuery.all.mockResolvedValue([])
    const result = await genomicElementSearch({ source_annotation: 'nonexistent', page: 0 })
    expect(result).toEqual([])
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('FILTER record.source_annotation == \'nonexistent\''))
  })

  test('genomicElementSearch with no parameters', async () => {
    mockQuery.all.mockResolvedValue([mockGenomicElement])
    const result = await genomicElementSearch({ page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('SORT record._key'))
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 25'))
    expect(result).toEqual([mockGenomicElement])
  })

  test('tRPC router integration', async () => {
    const expectedResult = {
      chr: 'chr1',
      start: 1157527,
      end: 1158185,
      name: 'ABC123',
      source_annotation: 'enhancer',
      type: 'candidate_cis_regulatory_element',
      source: 'ENCODE_EpiRaction',
      source_url: 'https://www.encodeproject.org/annotations/ENCSR831INH/'
    }
    mockQuery.all.mockResolvedValue([expectedResult])
    const caller = appRouter.createCaller({ requestId: 'test-request-id' })
    const result = await caller.genomicElements({ region: 'chr1:1157527-1158185' })

    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('OPTIONS { indexHint: "idx_zkd_start_end", forceIndexHint: true }'))
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('FILTER record.chr == \'chr1\' and record.start < 1158185 AND record.end > 1157527'))
    expect(result).toEqual([expectedResult])
    expect(db.query).toHaveBeenCalledTimes(1)
  })
})
