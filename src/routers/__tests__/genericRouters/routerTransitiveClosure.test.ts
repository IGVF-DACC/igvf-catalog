import mock = require('mock-fs')
import { db } from '../../../database'
import { configType, schemaConfigFilePath } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterTransitiveClosure } from '../../genericRouters/routerTransitiveClosure'

type routerType = typeof publicProcedure

const SCHEMA_CONFIG = `
variant to variant correlation:
  represented_as: edge
  inherit_properties: true
  label_in_input: topld
  label_as_edge: VARIANT_CORRELATION
  db_collection_name: variant_correlations
  db_collection_per_chromosome: false
  relationship:
    from: sequence variant
    to: sequence variant
  properties:
    chr: str
    ancestry: str

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

describe('routerTransitiveClosure', () => {
  afterEach(() => {
    mock.restore()
  })

  describe('constructor', () => {
    test('it parses config fields accordingly', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const schemaConfig = loadSchemaConfig()

      const router = new RouterTransitiveClosure(schemaConfig['variant to variant correlation'])

      expect(router.apiName).toEqual('topld/transitiveClosure')
      expect(router.path).toEqual('topld/transitiveClosure/{from}/{to}')
      expect(router.hasGetByIDEndpoint).toEqual(false)
      expect(router.fuzzyTextSearch).toEqual([])
      expect(router.edgeDBCollectionName).toEqual('variant_correlations')
    })
  })

  describe('getPaths', () => {
    let router: RouterTransitiveClosure
    let schemaConfig: Record<string, configType>

    beforeEach(() => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      schemaConfig = loadSchemaConfig()
    })

    test('queries correct DB collection and return matched records', async () => {
      class DB {
        public all (): any[] {
          return [{
            vertices: [
              {
                _key: 'vertix_1_key',
                _id: 'vertix_1',
                _rev: 'vertix_1_rev',
                uri: '/vertix_1',
                label: 'vertix 1',
                comment: 'vertix 1 comment'
              },
              {
                _key: 'vertix_2_key',
                _id: 'vertix_2',
                _rev: 'vertix_2_rev',
                uri: '/vertix_2',
                label: 'vertix 2',
                comment: 'vertix 2 comment'
              },
              {
                _key: 'vertix_3_key',
                _id: 'vertix_3',
                _rev: 'vertix_3_rev',
                uri: '/vertix_3',
                label: 'vertix 3',
                comment: 'vertix 3 comment'
              }
            ],
            edges: [
              {
                _key: 'edge_1_key',
                _id: 'edge_1',
                _from: 'vertix_1',
                _to: 'vertix_2',
                _rev: 'edge_1_rev',
                type: 'subClassOf'
              },
              {
                _key: 'edge_2_key',
                _id: 'edge_2',
                _from: 'vertix_2',
                _to: 'vertix_3',
                _rev: 'edge_2_rev',
                type: 'subClassOf'
              }
            ]
          }]
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      router = new RouterTransitiveClosure(schemaConfig['variant to variant correlation'])
      const records = await router.getPaths('vertex_1', 'vertex_3')

      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`${router.edgeDBCollectionName}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FOR path IN OUTBOUND ALL_SHORTEST_PATHS'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('\'vertex_1\' TO \'vertex_3\''))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('RETURN path'))

      const result = {
        paths: [
          [
            {
              from: 'vertix_1',
              to: 'vertix_2',
              type: 'subClassOf'
            },
            {
              from: 'vertix_2',
              to: 'vertix_3',
              type: 'subClassOf'
            }
          ]
        ],
        vertices: {
          vertix_1: {
            label: 'vertix 1',
            uri: '/vertix_1'
          },
          vertix_2: {
            label: 'vertix 2',
            uri: '/vertix_2'
          },
          vertix_3: {
            label: 'vertix 3',
            uri: '/vertix_3'
          }
        }
      }

      expect(records).toEqual(result)
    })

    test('decodes search term before querying', async () => {
      class DB {
        public all (): any[] {
          return []
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      router = new RouterTransitiveClosure(schemaConfig['variant to variant correlation'])

      await router.getPaths('brain%3AGO_0070257', 'spine%3AGO_0070258')

      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('IN OUTBOUND ALL_SHORTEST_PATHS'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('\'brain:GO_0070257\' TO \'spine:GO_0070258\''))
    })
  })

  describe('generateRouter', () => {
    let routerBuilder: RouterTransitiveClosure
    let router: routerType
    let openApi: any

    beforeEach(() => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const schemaConfig = loadSchemaConfig()

      routerBuilder = new RouterTransitiveClosure(schemaConfig['variant to variant correlation'])
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
