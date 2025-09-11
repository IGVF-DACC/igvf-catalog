import mock = require('mock-fs')
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { verboseItems, getDBReturnStatements, getFilterStatements, preProcessRegionParam, validRegion } from '../_helpers'
import { schemaConfigFilePath } from '../../../constants'
import { db } from '../../../database'
import { TRPCError } from '@trpc/server'

const SCHEMA_CONFIG = `
variant to genomic element:
  is_a: association
  represented_as: edge
  label_in_input: AFGR_caqtl
  label_as_edge: VARIANT_genomic_element
  db_collection_name: test_collection
  db_indexes:
    coordinates:
      type: zkd
      fields:
        - log10pvalue
        - beta, log10pvalue
    query:
      type: persistent
      fields:
        - source, label
        - label
  relationship:
    from: variants
    to: genomic_elements
  accessible_via:
    name: variants_genomic_elements
    filter_by: beta, log10pvalue, source, label
    filter_by_range: beta, log10pvalue
    return: beta, log10pvalue, source, source_url
  properties:
    label: str
    log10pvalue: int
    p_value: int
    beta: int
    source: str
    source_url: str
    biological_context: str
    biosample_term: str
    name: str
    inverse_name: str
    method: str
`

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

    const config: Record<string, string> = {}
    config[schemaConfigFilePath] = SCHEMA_CONFIG
    mock(config)
    const schema = loadSchemaConfig()['variant to genomic element']

    const mockResponse = [
      { _id: 'id1', name: 'Item 1' },
      { _id: 'id2', name: 'Item 2' }
    ]

    mockDbQuery.mockResolvedValueOnce({
      all: jest.fn().mockResolvedValueOnce(mockResponse)
    })

    const result = await verboseItems(ids, schema)

    expect(mockDbQuery).toHaveBeenCalledWith(`
    FOR record in test_collection
    FILTER record._id in ['id1','id2']
    RETURN {
      'beta': record['beta'], 'log10pvalue': record['log10pvalue'], 'source': record['source'], 'source_url': record['source_url']
    }`)
    expect(result).toEqual({
      id1: { _id: 'id1', name: 'Item 1' },
      id2: { _id: 'id2', name: 'Item 2' }
    })
  })

  it('should return an empty dictionary if no items are found', async () => {
    const ids = ['id1', 'id2']

    const config: Record<string, string> = {}
    config[schemaConfigFilePath] = SCHEMA_CONFIG
    mock(config)
    const schema = loadSchemaConfig()['variant to genomic element']

    mockDbQuery.mockResolvedValueOnce({
      all: jest.fn().mockResolvedValueOnce([])
    })

    const result = await verboseItems(ids, schema)

    expect(result).toEqual({})
  })
})

describe('getDBReturnStatements', () => {
  it('should generate a return statement for a schema', () => {
    const schema = {
      accessible_via: {
        return: '_id, name, age',
        simplified_return: '_id, name'
      }
    }

    const result = getDBReturnStatements(schema)

    expect(result).toEqual("_id: record._key, 'name': record['name'], 'age': record['age']")
  })

  it('should skip specified fields', () => {
    const schema = {
      accessible_via: {
        return: '_id, name, age',
        simplified_return: '_id, name'
      }
    }

    const result = getDBReturnStatements(schema, false, '', ['age'])

    expect(result).toEqual("_id: record._key, 'name': record['name']")
  })
})

describe('getFilterStatements', () => {
  it('should generate filter statements for query parameters', () => {
    const schema = {
      accessible_via: {
        filter_by_range: 'age'
      },
      properties: {
        name: 'string',
        age: 'int',
        is_active: 'boolean'
      }
    }

    const queryParams = {
      name: 'John',
      age: 'gte:30',
      is_active: true
    }

    const result = getFilterStatements(schema, queryParams)

    expect(result).toEqual(
      "record.name == 'John' and record['age'] >= 30 and record.is_active == true"
    )
  })

  it('should handle intersect filters', () => {
    const schema = {
      accessible_via: {
        filter_by_range: 'age'
      },
      properties: {}
    }

    const queryParams = {
      intersect: 'start-end:100-200'
    }

    const result = getFilterStatements(schema, queryParams)

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
