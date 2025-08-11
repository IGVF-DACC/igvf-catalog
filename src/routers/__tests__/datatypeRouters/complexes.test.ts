import { complexesRouters, complexSearch } from '../../datatypeRouters/nodes/complexes'
import { db } from '../../../database'
import { TRPCError } from '@trpc/server'
import { appRouter } from '../../_app'

// Mock the database
jest.mock('../../../database', () => ({
  db: {
    query: jest.fn()
  }
}))

// Mock data constants
const mockComplex = {
  _id: 'COMPLEX:12345',
  name: 'Test Complex',
  alias: ['Test Alias 1', 'Test Alias 2'],
  molecules: ['GENE1', 'GENE2'],
  evidence_code: 'ECO:0000269',
  experimental_evidence: 'Experimental evidence',
  description: 'A test protein complex',
  complex_assembly: 'Heterodimer',
  complex_source: 'Reactome',
  reactome_xref: ['R-HSA-12345'],
  source: 'Reactome',
  source_url: 'https://reactome.org/PathwayBrowser/#/R-HSA-12345'
}

describe('complexes router', () => {
  const mockQuery = { all: jest.fn() }

  beforeEach(() => {
    jest.clearAllMocks()
    ;(db.query as jest.Mock).mockReturnValue(mockQuery)
  })

  test('router structure', () => {
    const router = complexesRouters.complexes
    const openApi = router._def.meta?.openapi

    // Basic router structure
    expect('complexes' in complexesRouters).toBe(true)
    expect(router._def.query).toBeTruthy()
    expect(openApi?.method).toBe('GET')
    expect(openApi?.path).toBe('/complexes')
  })

  test('complexSearch error handling', async () => {
    // Missing required parameters
    await expect(complexSearch({})).rejects.toThrow(TRPCError)
    await expect(complexSearch({})).rejects.toThrow('At least one parameter must be defined.')

    // Complex ID not found
    mockQuery.all.mockResolvedValue([])
    await expect(complexSearch({ complex_id: 'INVALID_ID' })).rejects.toThrow(TRPCError)
    await expect(complexSearch({ complex_id: 'INVALID_ID' })).rejects.toThrow('Complex INVALID_ID not found.')
  })

  test('complexSearch by ID functionality', async () => {
    mockQuery.all.mockResolvedValue([mockComplex])

    // Test regular complex_id
    const result = await complexSearch({ complex_id: 'COMPLEX:12345' })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record._key == 'COMPLEX:12345'"))
    expect(result).toEqual(mockComplex)

    // Test URL encoded complex_id
    mockQuery.all.mockResolvedValue([{ _id: 'test', name: 'test' }])
    await complexSearch({ complex_id: 'COMPLEX%3A12345' })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record._key == 'COMPLEX:12345'"))
  })

  test('complexSearch by name functionality', async () => {
    // Name search returns results
    mockQuery.all.mockResolvedValue([mockComplex])
    const result = await complexSearch({ name: 'Test Complex' })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('SEARCH TOKENS("Test Complex", "text_en_no_stem") ALL in record.name'))
    expect(result).toEqual([mockComplex])
    expect(db.query).toHaveBeenCalledTimes(1)
  })

  test('complexSearch by description functionality', async () => {
    // Description search returns results
    mockQuery.all.mockResolvedValue([mockComplex])
    const result = await complexSearch({ description: 'protein complex' })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('SEARCH TOKENS("protein complex", "text_en_no_stem") ALL in record.description'))
    expect(result).toEqual([mockComplex])
    expect(db.query).toHaveBeenCalledTimes(1)
  })

  test('complexSearch by name and description functionality', async () => {
    // Combined name and description search
    mockQuery.all.mockResolvedValue([mockComplex])
    const result = await complexSearch({ name: 'Test Complex', description: 'protein complex' })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('SEARCH TOKENS("Test Complex", "text_en_no_stem") ALL in record.name AND TOKENS("protein complex", "text_en_no_stem") ALL in record.description'))
    expect(result).toEqual([mockComplex])
    expect(db.query).toHaveBeenCalledTimes(1)
  })

  test('complexSearch parameter handling', async () => {
    // Test pagination
    mockQuery.all.mockResolvedValue([])
    await complexSearch({ name: 'Test Complex', page: 1 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT'))
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT 25, 25'))

    // Test priority (complex_id over name/description)
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([mockComplex])
    const result = await complexSearch({ complex_id: 'COMPLEX:12345', name: 'Test Complex', description: 'protein complex' })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record._key == 'COMPLEX:12345'"))
    expect(db.query).not.toHaveBeenCalledWith(expect.stringContaining('SEARCH TOKENS'))
    expect(result).toEqual(mockComplex)
  })

  test('tRPC router integration', async () => {
    mockQuery.all.mockResolvedValue([mockComplex])
    const caller = appRouter.createCaller({ requestId: 'test-request-id' })
    const result = await caller.complexes({ name: 'Test Complex' })

    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('SEARCH TOKENS("Test Complex", "text_en_no_stem") ALL in record.name'))
    expect(result).toEqual([mockComplex])
    expect(db.query).toHaveBeenCalledTimes(1)
  })
})
