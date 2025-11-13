import { verboseItems, getDBReturnStatements, getFilterStatements, preProcessRegionParam, validRegion } from '../_helpers'
import { db } from '../../../database'
import { TRPCError } from '@trpc/server'
import { getSchema } from '../schema'

// Use real schema file for testing
const GENES_PATHWAYS_SCHEMA = getSchema('data/schemas/edges/genes_pathways.Reactome.json')
const GENES_SCHEMA = getSchema('data/schemas/nodes/genes.GencodeGene.json')

// Mock the database query
jest.mock('../../../database', () => ({
  db: {
    query: jest.fn()
  }
}))

const mockDbQuery = db.query as jest.Mock

describe('verboseItems', () => {
  it('should return a dictionary of items from the database', async () => {
    const ids = ['id1', 'id2']

    const mockResponse = [
      { _id: 'id1', name: 'Item 1' },
      { _id: 'id2', name: 'Item 2' }
    ]

    mockDbQuery.mockResolvedValueOnce({
      all: jest.fn().mockResolvedValueOnce(mockResponse)
    })

    const result = await verboseItems(ids, GENES_PATHWAYS_SCHEMA)

    expect(mockDbQuery).toHaveBeenCalledWith(`
    FOR record in genes_pathways
    FILTER record._id in ['id1','id2']
    RETURN {
      'source': record['source'], 'source_url': record['source_url'], 'organism': record['organism']
    }`)
    expect(result).toEqual({
      id1: { _id: 'id1', name: 'Item 1' },
      id2: { _id: 'id2', name: 'Item 2' }
    })
  })

  it('should return an empty dictionary if no items are found', async () => {
    const ids = ['id1', 'id2']

    mockDbQuery.mockResolvedValueOnce({
      all: jest.fn().mockResolvedValueOnce([])
    })

    const result = await verboseItems(ids, GENES_PATHWAYS_SCHEMA)

    expect(result).toEqual({})
  })
})

describe('getDBReturnStatements', () => {
  it('should generate a return statement for a schema', () => {
    const result = getDBReturnStatements(GENES_PATHWAYS_SCHEMA)

    // Should return the fields from accessible_via.return: source, source_url, organism
    expect(result).toContain('source')
    expect(result).toContain('source_url')
    expect(result).toContain('organism')
  })

  it('should skip specified fields', () => {
    const result = getDBReturnStatements(GENES_PATHWAYS_SCHEMA, false, '', ['organism'])

    // Should not include organism
    expect(result).not.toContain('organism')
    expect(result).toContain('source')
    expect(result).toContain('source_url')
  })
})

describe('getFilterStatements', () => {
  it('should generate filter statements for query parameters', () => {
    const queryParams = {
      source: 'Reactome',
      organism: 'Homo sapiens'
    }

    const result = getFilterStatements(GENES_PATHWAYS_SCHEMA, queryParams)

    expect(result).toContain("record.source == 'Reactome'")
    expect(result).toContain("record.organism == 'Homo sapiens'")
  })

  it('should handle intersect filters', () => {
    // Use a schema with start/end fields for intersect testing

    const queryParams = {
      intersect: 'start-end:100-200'
    }

    const result = getFilterStatements(GENES_SCHEMA, queryParams)

    expect(result).toEqual(
      'record.start < 200 AND record.end > 100'
    )
  })
})

describe('preProcessRegionParam', () => {
  it('should process region parameters and return updated input', () => {
    const input = { region: 'chr1:100-200' }
    const result = preProcessRegionParam(input)

    expect(result).toEqual({
      chr: 'chr1',
      intersect: 'start-end:100-200'
    })
  })

  it('should throw an error for invalid region format', () => {
    const input = { region: 'invalid_region' }

    expect(() => preProcessRegionParam(input)).toThrow(TRPCError)
  })
})

describe('validRegion', () => {
  it('should return breakdown for valid region format', () => {
    const result = validRegion('chr1:100-200')
    expect(result?.slice(0, 4)).toStrictEqual(['chr1:100-200', 'chr1', '100', '200'])
  })

  it('should return null for invalid region format', () => {
    const result = validRegion('invalid_region')

    expect(result).toBeNull()
  })
})
