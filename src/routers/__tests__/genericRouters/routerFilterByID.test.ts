import mock = require('mock-fs')
import { db } from '../../../database'
import { schemaConfigFilePath } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'

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

describe('routerFilterByID', () => {
  afterEach(() => {
    mock.restore()
  })

  describe('constructor', () => {
    test('it parses config fields accordingly', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const schemaConfig = loadSchemaConfig()['sequence variant']

      const router = new RouterFilterByID(schemaConfig)

      expect(router.apiName).toEqual('variants_id')
      expect(router.path).toEqual('variants/{id}')
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
      expect(router.hasGetByIDEndpoint).toEqual(false)
      expect(router.dbCollectionName).toEqual('variants')
      expect(router.dbCollectionPerChromosome).toEqual(false)
      expect(router.dbReturnStatements).toEqual("_id: record._key, 'chr': record['chr'], 'pos': record['pos:long']")
    })
  })

  describe('getObjectById', () => {
    let router: RouterFilterByID

    beforeEach(() => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const schemaConfig = loadSchemaConfig()['sequence variant']

      router = new RouterFilterByID(schemaConfig)
    })

    test('queries correct DB collection and return records', async () => {
      class DB {
        public all (): any[] {
          return ['record']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      const records = await router.getObjectById('random_ID:value')
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`IN ${router.dbCollectionName}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("record._key == 'random_ID:value'"))
      expect(records).toEqual('record')
    })

    test('decodes ID value before querying', async () => {
      class DB {
        public all (): any[] {
          return ['record']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      const records = await router.getObjectById('obo%3AGO_0070257')
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`IN ${router.dbCollectionName}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("record._key == 'obo:GO_0070257'"))
      expect(records).toEqual('record')
    })

    test('raises not found TRPC Error if ID is not found', async () => {
      class DB {
        public all (): any[] {
          return []
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })

      jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      try {
        await router.getObjectById('random_ID_value')
      } catch (e: any) {
        expect(e.code).toEqual('NOT_FOUND')
        expect(e.message).toEqual('Record random_ID_value not found.')
        return
      }

      fail('getObjectById should have raised error if ID was not found')
    })
  })

  describe('generateRouter', () => {
    let routerBuilder: RouterFilterByID
    let router: routerType
    let openApi: any

    beforeEach(() => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const schemaConfig = loadSchemaConfig()['sequence variant']

      routerBuilder = new RouterFilterByID(schemaConfig)
      router = routerBuilder.generateRouter()
      openApi = router._def.meta?.openapi
    })

    test('implements OpenApi protocol', () => {
      expect(typeof openApi).toBe('object')
    })

    test('has correct URL', () => {
      expect(openApi?.method).toBe('GET')
      expect(openApi?.path).toBe(`/${routerBuilder.path}`)
    })

    test('Expects procedure to be a trpc query', () => {
      expect(router._def.query).toBeTruthy()
    })
  })
})
