import { drugsRouters, drugSearch } from '../../datatypeRouters/nodes/drugs'
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
const mockDrug = {
  _id: 'CHEBI:15365',
  name: 'aspirin',
  drug_ontology_terms: ['CHEBI:15365'],
  source: 'ChEBI',
  source_url: 'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:15365'
}

describe('drugs router', () => {
  const mockQuery = { all: jest.fn() }

  beforeEach(() => {
    jest.clearAllMocks()
    ;(db.query as jest.Mock).mockReturnValue(mockQuery)
  })

  test('router structure', () => {
    const router = drugsRouters.drugs
    const openApi = router._def.meta?.openapi

    // Basic router structure
    expect('drugs' in drugsRouters).toBe(true)
    expect(router._def.query).toBeTruthy()
    expect(openApi?.method).toBe('GET')
    expect(openApi?.path).toBe('/drugs')
  })

  test('drugSearch error handling', async () => {
    // Missing required parameters
    await expect(drugSearch({})).rejects.toThrow(TRPCError)
    await expect(drugSearch({})).rejects.toThrow('Either drug_id or name must be defined.')

    // Drug ID not found
    mockQuery.all.mockResolvedValue([])
    await expect(drugSearch({ drug_id: 'INVALID_ID' })).rejects.toThrow(TRPCError)
    await expect(drugSearch({ drug_id: 'INVALID_ID' })).rejects.toThrow('Record INVALID_ID not found.')
  })

  test('drugSearch by ID functionality', async () => {
    mockQuery.all.mockResolvedValue([mockDrug])

    // Test regular drug_id
    const result = await drugSearch({ drug_id: 'CHEBI:15365' })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record._key == 'CHEBI:15365'"))
    expect(result).toEqual(mockDrug)

    // Test URL encoded drug_id
    mockQuery.all.mockResolvedValue([{ _id: 'test', name: 'test' }])
    await drugSearch({ drug_id: 'CHEBI%3A15365' })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record._key == 'CHEBI:15365'"))
  })

  test('drugSearch by name functionality', async () => {
    // Token search returns results
    mockQuery.all.mockResolvedValue([mockDrug])
    const result = await drugSearch({ name: 'aspirin' })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('SEARCH TOKENS("aspirin", "text_en_no_stem") ALL in record.name'))
    expect(result).toEqual([mockDrug])
    expect(db.query).toHaveBeenCalledTimes(1)

    // Token search returns empty, falls back to fuzzy search
    mockQuery.all
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([{ _id: 'test', name: 'aspirin' }])

    const fuzzyResult = await drugSearch({ name: 'aspirin' })
    expect(db.query).toHaveBeenCalledTimes(3) // 1 from above + 2 for fuzzy search
    expect(db.query).toHaveBeenNthCalledWith(2, expect.stringContaining('SEARCH TOKENS("aspirin", "text_en_no_stem") ALL in record.name'))
    expect(db.query).toHaveBeenNthCalledWith(3, expect.stringContaining('SEARCH LEVENSHTEIN_MATCH'))
    expect(fuzzyResult).toEqual([{ _id: 'test', name: 'aspirin' }])

    // Both searches return empty
    mockQuery.all
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])

    const emptyResult = await drugSearch({ name: 'nonexistent_drug' })
    expect(emptyResult).toEqual([])
  })

  test('drugSearch parameter handling', async () => {
    // Test limit parameter
    mockQuery.all.mockResolvedValue([])
    await drugSearch({ name: 'aspirin', limit: 50, page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 50'))

    // Test limit capping
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([])
    await drugSearch({ name: 'aspirin', limit: 150, page: 0 })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT'))
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('LIMIT 0, 100'))

    // Test priority (drug_id over name)
    jest.clearAllMocks()
    mockQuery.all.mockResolvedValue([mockDrug])
    const result = await drugSearch({ drug_id: 'CHEBI:15365', name: 'aspirin' })
    expect(db.query).toHaveBeenCalledWith(expect.stringContaining("FILTER record._key == 'CHEBI:15365'"))
    expect(db.query).not.toHaveBeenCalledWith(expect.stringContaining('SEARCH TOKENS'))
    expect(result).toEqual(mockDrug)
  })

  test('tRPC router integration', async () => {
    mockQuery.all.mockResolvedValue([mockDrug])
    const caller = appRouter.createCaller({ requestId: 'test-request-id' })
    const result = await caller.drugs({ name: 'aspirin' })

    expect(db.query).toHaveBeenCalledWith(expect.stringContaining('SEARCH TOKENS("aspirin", "text_en_no_stem") ALL in record.name'))
    expect(result).toEqual([mockDrug])
    expect(db.query).toHaveBeenCalledTimes(1)
  })
})
