import mock = require('mock-fs')
import { z } from 'zod'
import { db } from '../../../database'
import { schemaConfigFilePath } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'

type routerType = typeof publicProcedure

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
    return: _id, chr, pos
  properties:
    chr: str
    pos: int
    start: int
    end: int
    active: boolean
`

const SCHEMA_CONFIG_NO_RANGE = `
sequence variant:
  represented_as: node
  label_in_input: gnomad
  db_collection_name: variants
  db_collection_per_chromosome: false
  accessible_via:
    name: variants
    description: 'Retrieve variants data. Example: chr = chr1'
    filter_by: _id, chr, pos
    return: _id, chr, pos
  properties:
    chr: str
    pos: int
`

describe('routerFilterBy', () => {
  afterEach(() => {
    mock.restore()
  })

  describe('constructor', () => {
    test('it parses config fields accordingly', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const schemaConfig = loadSchemaConfig()['sequence variant']

      const router = new RouterFilterBy(schemaConfig)

      expect(router.apiName).toEqual('variants')
      expect(router.apiSpecs).toEqual({
        name: 'variants',
        description: 'Retrieve variants data. Example: chr = chr1',
        filter_by: '_id, chr',
        filter_by_range: 'start, end, pos',
        return: '_id, chr, pos'
      })
      expect(router.properties).toEqual({
        chr: 'str',
        pos: 'int',
        start: 'int',
        end: 'int',
        active: 'boolean'
      })
      expect(router.filterBy).toEqual(['_id', 'chr'])
      expect(router.filterByRange).toEqual(['start', 'end', 'pos'])
      expect(router.output).toEqual(['_id', 'chr', 'pos'])
      expect(router.hasGetByIDEndpoint).toEqual(true)
      expect(router.dbCollectionName).toEqual('variants')
      expect(router.dbCollectionPerChromosome).toEqual(false)
      expect(router.dbReturnStatements).toEqual("_id: record._key, 'chr': record['chr'], 'pos': record['pos:long']")
    })

    test('it loads empty range fields if filterByRange is not present', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG_NO_RANGE
      mock(config)

      const schemaConfig = loadSchemaConfig()['sequence variant']

      const router = new RouterFilterBy(schemaConfig)
      expect(router.filterByRange).toEqual([])
    })
  })

  describe('getFilterStatements', () => {
    let router: RouterFilterBy

    beforeEach(() => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const schemaConfig = loadSchemaConfig()['sequence variant']

      router = new RouterFilterBy(schemaConfig)
    })

    test('loads all valid query params and ignore undefined values', () => {
      const queryParams = {
        chr: 'chr8',
        invalidParam: undefined
      }

      const filterSts = router.getFilterStatements(queryParams)
      expect(filterSts).toEqual("record.chr == 'chr8'")
    })

    test('ignores reserved pagination query params', () => {
      const queryParams = {
        page: 1,
        sort: 'chr'
      }

      const filterSts = router.getFilterStatements(queryParams)
      expect(filterSts).toBe('')
    })

    test('loads all range query params appending :long suffix', () => {
      const queryParams = {
        chr: 'chr8',
        start: 12345,
        end: 54321
      }

      const filterSts = router.getFilterStatements(queryParams)
      expect(filterSts).toEqual("record.chr == 'chr8' and record['start:long'] == 12345 and record['end:long'] == 54321")
    })

    test('supports range query for single property', () => {
      const queryParams = { pos: 'range:12345-54321' }
      let filterSts = router.getFilterStatements(queryParams)
      expect(filterSts).toEqual("record['pos:long'] >= 12345 and record['pos:long'] <= 54321")

      const annotationQueryParams = { 'annotations.freq.1000genome.alt': 'range:0.5-1' }
      filterSts = router.getFilterStatements(annotationQueryParams)
      expect(filterSts).toEqual("record.annotations.freq['1000genome']['alt:long'] >= 0.5 and record.annotations.freq['1000genome']['alt:long'] <= 1")
    })

    test('uses correct operators for region search', () => {
      let queryParams = { chr: 'chr8', start: '12345', end: '54321' }
      let filterSts = router.getFilterStatements(queryParams)
      expect(filterSts).toEqual("record.chr == 'chr8' and record['start:long'] == 12345 and record['end:long'] == 54321")

      queryParams = { chr: 'chr8', start: 'gt:12345', end: 'gt:54321' }
      filterSts = router.getFilterStatements(queryParams)
      expect(filterSts).toEqual("record.chr == 'chr8' and record['start:long'] > 12345 and record['end:long'] > 54321")

      queryParams = { chr: 'chr8', start: 'gte:12345', end: 'gte:54321' }
      filterSts = router.getFilterStatements(queryParams)
      expect(filterSts).toEqual("record.chr == 'chr8' and record['start:long'] >= 12345 and record['end:long'] >= 54321")

      queryParams = { chr: 'chr8', start: 'lt:12345', end: 'lt:54321' }
      filterSts = router.getFilterStatements(queryParams)
      expect(filterSts).toEqual("record.chr == 'chr8' and record['start:long'] < 12345 and record['end:long'] < 54321")

      queryParams = { chr: 'chr8', start: 'lte:12345', end: 'lte:54321' }
      filterSts = router.getFilterStatements(queryParams)
      expect(filterSts).toEqual("record.chr == 'chr8' and record['start:long'] <= 12345 and record['end:long'] <= 54321")
    })
  })

  describe('getObjects', () => {
    let router: RouterFilterBy

    beforeEach(() => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const schemaConfig = loadSchemaConfig()['sequence variant']

      router = new RouterFilterBy(schemaConfig)
    })

    test('queries correct DB collection and return records', async () => {
      class DB {
        public all (): any[] {
          return ['records']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      const queryParams = { chr: 'chr1' }
      const records = await router.getObjects(queryParams)
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`IN ${router.dbCollectionName}`))
      expect(records).toEqual(['records'])
    })

    test('adds sorting parameter when specified', async () => {
      class DB {
        public all (): any[] {
          return ['records']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      const queryParams = { chr: 'chr1', sort: 'chr' }
      const records = await router.getObjects(queryParams)
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SORT record['chr']"))
      expect(records).toEqual(['records'])
    })

    test('adds query options when passed', async () => {
      class DB {
        public all (): any[] {
          return ['records']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      const queryParams = { chr: 'chr1', sort: 'chr' }
      const queryOptions = 'OPTIONS { indexHint: "region", forceIndexHint: true }'
      const records = await router.getObjects(queryParams, queryOptions)
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(queryOptions))
      expect(records).toEqual(['records'])
    })
  })

  describe('resolveTypes', () => {
    let router: RouterFilterBy

    beforeEach(() => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const schemaConfig = loadSchemaConfig()['sequence variant']

      router = new RouterFilterBy(schemaConfig)
    })

    test('parses IDs to correct ZOD types ignoring id field', () => {
      const types = z.object(router.resolveTypes(['_id', 'chr', 'start', 'end', 'active'], false, false))

      const exampleData = {
        chr: 'chr1',
        start: 123,
        end: 321,
        active: true
      }
      const parsedObj = types.parse(exampleData)
      expect(parsedObj).toEqual(exampleData)

      const exampleDataWithID = { ...exampleData, _id: '123' }
      expect(types.parse(exampleDataWithID)).toEqual(exampleData)
    })

    test('parses IDs to correct ZOD types adding id field', () => {
      const types = z.object(router.resolveTypes(['_id', 'chr', 'start', 'end', 'active'], true, false))

      const exampleData = {
        _id: '123',
        chr: 'chr1',
        start: 123,
        end: 321,
        active: true
      }

      const parsedObj = types.parse(exampleData)
      expect(parsedObj).toEqual(exampleData)
    })

    test('defaults to string.optional', () => {
      const types = z.object(router.resolveTypes(['chr', 'field_not_in_schema'], false, false))

      const exampleData = {
        chr: 'chr1',
        field_not_in_schema: 'defaults to string'
      }

      const parsedObj = types.parse(exampleData)
      expect(parsedObj).toEqual(exampleData)
    })

    test('sets all fields to string when specified', () => {
      const types = z.object(router.resolveTypes(['_id', 'chr', 'start', 'end', 'active'], true, true))

      const exampleData = {
        _id: '123',
        chr: 'chr1',
        start: '123',
        end: '321',
        active: 'true'
      }

      const parsedObj = types.parse(exampleData)
      expect(parsedObj).toEqual(exampleData)
    })
  })

  describe('generateRouter', () => {
    let routerBuilder: RouterFilterBy
    let router: routerType
    let openApi: any

    beforeEach(() => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const schemaConfig = loadSchemaConfig()['sequence variant']

      routerBuilder = new RouterFilterBy(schemaConfig)
      router = routerBuilder.generateRouter()
      openApi = router._def.meta?.openapi
    })

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe(`/${routerBuilder.apiName}`)
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })
})
