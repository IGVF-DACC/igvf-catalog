import mock = require('mock-fs')

import { schemaConfigFilePath, configType } from '../../constants'
import { loadSchemaConfig } from '../genericRouters/genericRouters'
import { validRegion, preProcessRegionParam, getFilterStatements, getDBReturnStatements } from '../datatypeRouters/_helpers'

const SCHEMA_CONFIG = `
sequence variant:
  represented_as: node
  label_in_input: gnomad
  db_collection_name: variants
  db_collection_per_chromosome: false
  accessible_via:
    name: variants
    description: 'Retrieve variants data. Example: chr = chr1'
    filter_by: _id, chr
    filter_by_range: start, end, pos
    simplified_return: chr, pos
    return: _id, chr, pos
  properties:
    chr: str
    pos: int
    start: int
    end: int
    active: boolean
`

describe('.validRegion', () => {
  test('returns null for invalid region', () => {
    expect(validRegion('myInvalidRegion')).toBe(null)
  })

  test('returns null if region is valid but incomplete', () => {
    expect(validRegion('chr1:123')).toBe(null)
  })

  test('returns correct components for valid region', () => {
    const chr = 'chr22'
    const start = '123'
    const end = '321'
    const region = `${chr}:${start}-${end}`

    const breakdown = validRegion(region) as string[]

    expect(breakdown[1]).toBe(chr)
    expect(breakdown[2]).toBe(start)
    expect(breakdown[3]).toBe(end)
  })
})

describe('.preProcessRegionParam', () => {
  test('takes an input with a region string and break down into intersect components', () => {
    const input = {
      region: 'chr1:12345-54321',
      other: 'parameter',
      another: 'parameter too'
    }

    const processed = preProcessRegionParam(input)

    expect(processed.chr).toBe('chr1')
    expect(processed.intersect).toBe('start-end:12345-54321')
  })

  test('removes old region parameter', () => {
    const input = {
      region: 'chr1:12345-54321',
      other: 'parameter',
      another: 'parameter too'
    }

    const processed = preProcessRegionParam(input)

    expect(processed.region).toBe(undefined)
    expect(processed.other).toBe('parameter')
    expect(processed.another).toBe('parameter too')
  })

  test('fails if parameter is invalid', () => {
    const input = {
      region: '1:12345-54321'
    }

    try {
      preProcessRegionParam(input)
    } catch {
      expect(true).toBe(true)
      return
    }

    fail('Invalid region format raise exception for no query params')
  })

  test('should not fail if parameter is not present', () => {
    const input = {
      other: 'parameter',
      another: 'parameter too'
    }

    try {
      preProcessRegionParam(input)
    } catch {
      throw new Error('Should not raise exception')
    }

    expect(true).toBe(true)
  })

  test('sets a range if single field is passed', () => {
    const input = {
      region: 'chr1:12345-54321'
    }

    const processed = preProcessRegionParam(input, 'position')
    expect(processed.position).toBe('range:12345-54321')
    expect(processed.chr).toBe('chr1')

    expect(processed.region).toBe(undefined)
    expect(processed.start).toBe(undefined)
    expect(processed.end).toBe(undefined)
  })

  test('sets a prefix name for range fields if passed', () => {
    const input = {
      intron_region: 'chr1:12345-54321'
    }

    const processed = preProcessRegionParam(input, null, 'intron')
    expect(processed.intron_chr).toBe('chr1')
    expect(processed.intersect).toBe('intron_start-intron_end:12345-54321')
  })
})

describe('getFilterStatements', () => {
  let schema: configType

  beforeEach(() => {
    const config: Record<string, string> = {}
    config[schemaConfigFilePath] = SCHEMA_CONFIG
    mock(config)

    schema = loadSchemaConfig()['sequence variant']
  })

  test('loads all valid query params and ignore undefined values', () => {
    const queryParams = {
      chr: 'chr8',
      invalidParam: undefined
    }
    const filterSts = getFilterStatements(schema, queryParams)
    expect(filterSts).toEqual("record.chr == 'chr8'")
  })

  test('ignores reserved pagination query params', () => {
    const queryParams = {
      page: 1,
      sort: 'chr'
    }

    const filterSts = getFilterStatements(schema, queryParams)
    expect(filterSts).toBe('')
  })

  test('loads all range query params', () => {
    const queryParams = {
      chr: 'chr8',
      start: 12345,
      end: 54321
    }

    const filterSts = getFilterStatements(schema, queryParams)
    expect(filterSts).toEqual("record.chr == 'chr8' and record['start'] == 12345 and record['end'] == 54321")
  })

  test('supports range query for single property', () => {
    const queryParams = { pos: 'range:12345-54321' }
    let filterSts = getFilterStatements(schema, queryParams)
    expect(filterSts).toEqual('record.pos >= 12345 and record.pos < 54321')

    const annotationQueryParams = { 'annotations.bravo_af': 'range:0.5-1' }
    filterSts = getFilterStatements(schema, annotationQueryParams)
    expect(filterSts).toEqual('record.annotations.bravo_af >= 0.5 and record.annotations.bravo_af < 1')
  })

  test('uses correct operators for region search', () => {
    let queryParams = { chr: 'chr8', start: '12345', end: '54321' }
    let filterSts = getFilterStatements(schema, queryParams)
    expect(filterSts).toEqual("record.chr == 'chr8' and record['start'] == 12345 and record['end'] == 54321")

    queryParams = { chr: 'chr8', start: 'gt:12345', end: 'gt:54321' }
    filterSts = getFilterStatements(schema, queryParams)
    expect(filterSts).toEqual("record.chr == 'chr8' and record['start'] > 12345 and record['end'] > 54321")

    queryParams = { chr: 'chr8', start: 'gte:12345', end: 'gte:54321' }
    filterSts = getFilterStatements(schema, queryParams)
    expect(filterSts).toEqual("record.chr == 'chr8' and record['start'] >= 12345 and record['end'] >= 54321")

    queryParams = { chr: 'chr8', start: 'lt:12345', end: 'lt:54321' }
    filterSts = getFilterStatements(schema, queryParams)
    expect(filterSts).toEqual("record.chr == 'chr8' and record['start'] < 12345 and record['end'] < 54321")

    queryParams = { chr: 'chr8', start: 'lte:12345', end: 'lte:54321' }
    filterSts = getFilterStatements(schema, queryParams)
    expect(filterSts).toEqual("record.chr == 'chr8' and record['start'] <= 12345 and record['end'] <= 54321")
  })
})

describe('getDBReturnStatements', () => {
  let schema: configType

  beforeEach(() => {
    const config: Record<string, string> = {}
    config[schemaConfigFilePath] = SCHEMA_CONFIG
    mock(config)

    schema = loadSchemaConfig()['sequence variant']
  })

  test('generates correct return statements based on schema', () => {
    const returns = getDBReturnStatements(schema)
    expect(returns).toEqual("_id: record._key, 'chr': record['chr'], 'pos': record['pos']")
  })

  test('generates simplified returns based on schema', () => {
    const returns = getDBReturnStatements(schema, true)
    expect(returns).toEqual("'chr': record['chr'], 'pos': record['pos']")
  })

  test('returns custom extra return when provided', () => {
    const returns = getDBReturnStatements(schema, true, "field: record['field']")
    expect(returns).toEqual("'chr': record['chr'], 'pos': record['pos'], field: record['field']")
  })

  test('removes fields if skipFields param is passed', () => {
    const returns = getDBReturnStatements(schema, true, '', ['pos'])
    expect(returns).toEqual("'chr': record['chr']")
  })
})
