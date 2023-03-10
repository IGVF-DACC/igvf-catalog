import mock = require('mock-fs')
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
    filter_by: _id, chr, pos
    filter_by_range: start, end
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
        filter_by: '_id, chr, pos',
        filter_by_range: 'start, end',
        return: '_id, chr, pos'
      })
      expect(router.properties).toEqual({
        chr: 'str',
        pos: 'int',
        start: 'int',
        end: 'int',
        active: 'boolean'
      })
      expect(router.filterBy).toEqual(['_id', 'chr', 'pos'])
      expect(router.filterByRange).toEqual(['start', 'end'])
      expect(router.output).toEqual(['_id', 'chr', 'pos'])
      expect(router.hasGetByIDEndpoint).toEqual(true)
      expect(router.dbCollectionName).toEqual('variants')
      expect(router.dbCollectionPerChromosome).toEqual(false)
      expect(router.dbReturnStatements).toEqual("_id: record._key, 'chr': record['chr'], pos: record['pos:long']")
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

    test('loads all range query params appending :long suffix', () => {
      const queryParams = {
        chr: 'chr8',
        start: 12345,
        end: 54321
      }

      const filterSts = router.getFilterStatements(queryParams)
      expect(filterSts).toEqual("record.chr == 'chr8' and record['start:long'] >= 12345 and record['end:long'] <= 54321")
    })

    test('raises error if no filter is specified', () => {
      const queryParams = {}

      try {
        router.getFilterStatements(queryParams)
      } catch {
        expect(true).toBe(true)
        return
      }

      fail('Endpoint should raise exception for no query params')
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
      const types = router.resolveTypes(['_id', 'chr', 'start', 'end', 'active'], false)

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
      const types = router.resolveTypes(['_id', 'chr', 'start', 'end', 'active'], true)

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
      const types = router.resolveTypes(['chr', 'field_not_in_schema'], false)

      const exampleData = {
        chr: 'chr1',
        field_not_in_schema: 'defaults to string'
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
