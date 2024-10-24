import mock = require('mock-fs')
import { db } from '../../../database'
import { configType, schemaConfigFilePath, QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFuzzy } from '../../genericRouters/routerFuzzy'

type routerType = typeof publicProcedure

const SCHEMA_CONFIG = `
cl class:
  represented_as: node
  label_in_input: cl_class
  db_collection_name: cl_classes
  accessible_via:
    name: cl_ontology
    filter_by: _id, label
    fuzzy_text_search: label
    return: _id, uri, label
  properties:
    uri: str
    label: str

protein:
    represented_as: node
    label_in_input: protein
    db_collection_name: proteins
    accessible_via:
      name: proteins
      filter_by: _id
      fuzzy_text_search: dbxrefs[*]
      return: _id, dbxrefs
    properties:
      dbxrefs: array
`

describe('routerFuzzy', () => {
  afterEach(() => {
    mock.restore()
  })

  describe('constructor', () => {
    test('it parses config fields accordingly', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const schemaConfig = loadSchemaConfig()

      const router = new RouterFuzzy(schemaConfig['cl class'])

      expect(router.apiName).toEqual('cl_ontology')
      expect(router.path).toEqual('cl_ontology/search/{term}')
      expect(router.apiSpecs).toEqual({
        name: 'cl_ontology',
        filter_by: '_id, label',
        fuzzy_text_search: 'label',
        return: '_id, uri, label'
      })
      expect(router.properties).toEqual({
        label: 'str',
        uri: 'str'
      })
      expect(router.filterBy).toEqual(['_id', 'label'])
      expect(router.output).toEqual(['_id', 'uri', 'label'])
      expect(router.hasGetByIDEndpoint).toEqual(false)
      expect(router.dbCollectionName).toEqual('cl_classes')
      expect(router.dbCollectionPerChromosome).toEqual(false)
      expect(router.dbReturnStatements).toEqual("_id: record._key, 'uri': record['uri'], 'label': record['label']")
    })
  })

  describe('searchViewName', () => {
    let router: RouterFuzzy
    let schemaConfig: Record<string, configType>

    beforeEach(() => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      schemaConfig = loadSchemaConfig()
      router = new RouterFuzzy(schemaConfig['cl class'])
    })

    test('builds correct ArangoDB search view alias', () => {
      expect(router.searchViewName()).toBe('cl_classes_fuzzy_search_alias')
    })
  })

  describe('autocompleteSearch', () => {
    let router: RouterFuzzy
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
          return ['record']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      router = new RouterFuzzy(schemaConfig['cl class'])
      const page = 0
      const records = await router.autocompleteSearch('brain', page)

      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`IN ${router.searchViewName()}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SEARCH STARTS_WITH(record['label'], \"brain\")"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('SORT BM25(record) DESC'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`LIMIT ${page}, ${QUERY_LIMIT}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN { ${router.dbReturnStatements} }`))

      expect(records).toEqual(['record'])
    })

    test('returns api response format', async () => {
      class DB {
        public all (): any[] {
          return ['record']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      router = new RouterFuzzy(schemaConfig['cl class'])
      const page = 0
      const records = await router.autocompleteSearch('brain', page, true)

      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`IN ${router.searchViewName()}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("SEARCH STARTS_WITH(record['label'], \"brain\")"))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('SORT BM25(record) DESC'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`LIMIT ${page}, ${QUERY_LIMIT}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`RETURN { term: record['${router.fuzzyTextSearch[0]}'], uri: CONCAT('/${router.apiName}/', record['_key']) }`))

      expect(records).toEqual(['record'])
    })

    test('supports custom filter', async () => {
      class DB {
        public all (): any[] {
          return ['record']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      router = new RouterFuzzy(schemaConfig['cl class'])
      const page = 0
      const records = await router.autocompleteSearch('brain', page, false, 'LEN(record.label) > 5')

      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('FILTER LEN(record.label) > 5'))

      expect(records).toEqual(['record'])
    })
  })

  describe('textSearch', () => {
    let router: RouterFuzzy
    let schemaConfig: Record<string, configType>

    beforeEach(() => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      schemaConfig = loadSchemaConfig()
    })

    describe('uses correct text search method', () => {
      const page = 0
      class DB {
        public all (): any[] {
          return ['record']
        }
      }
      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })

      beforeEach(() => {
        router = new RouterFuzzy(schemaConfig['cl class'])
      })

      afterEach(() => {
        mock.restore()
      })

      test('fuzzy search', async () => {
        const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)
        const records = await router.textSearch({ label: 'brain' }, 'fuzzy', page)
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('SEARCH LEVENSHTEIN_MATCH'))
        expect(records).toEqual(['record'])
      })

      test('autocomplete search', async () => {
        const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)
        const records = await router.textSearch({ label: 'brain' }, 'autocomplete', page)
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('SEARCH STARTS_WITH(record[\'label\'], "brain")'))
        expect(records).toEqual(['record'])
      })

      test('multiple tokens', async () => {
        const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)
        const records = await router.textSearch({ label: 'brain' }, 'token', page)
        expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('SEARCH TOKENS("brain", "text_en_no_stem") ALL in record.label'))
        expect(records).toEqual(['record'])
      })
    })

    test('takes multiple fields', async () => {
      class DB {
        public all (): any[] {
          return ['record']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      router = new RouterFuzzy(schemaConfig['cl class'])
      const page = 0
      const records = await router.textSearch({ label: 'brain', name: 'brain term' }, 'tokens', page)

      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('SEARCH TOKENS("brain", "text_en_no_stem") ALL in record.label'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('AND TOKENS("brain term", "text_en_no_stem") ALL in record.name'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`LIMIT ${page}, ${QUERY_LIMIT}`))

      expect(records).toEqual(['record'])
    })

    test('queries correct DB collection and return matched records', async () => {
      class DB {
        public all (): any[] {
          return ['record']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      router = new RouterFuzzy(schemaConfig['cl class'])
      const page = 0
      const records = await router.textSearch({ label: 'brain' }, 'fuzzy', page)

      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`IN ${router.searchViewName()}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('SEARCH LEVENSHTEIN_MATCH'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('record.label'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('TOKENS("brain", "text_en_no_stem")'))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`LIMIT ${page}, ${QUERY_LIMIT}`))

      expect(records).toEqual(['record'])
    })

    test('decodes search term before querying', async () => {
      class DB {
        public all (): any[] {
          return ['record']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      router = new RouterFuzzy(schemaConfig['cl class'])

      const page = 0
      await router.textSearch({ label: 'brain%3AGO_0070257' }, 'fuzzy', page)

      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`IN ${router.searchViewName()}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('TOKENS("brain:GO_0070257", "text_en_no_stem")'))
    })

    test('accepts custom filters', async () => {
      class DB {
        public all (): any[] {
          return ['record']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      router = new RouterFuzzy(schemaConfig['cl class'])

      const page = 0
      await router.textSearch({ label: 'brain%3AGO_0070257' }, 'fuzzy', page, "record.label == 'brainz'")

      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`IN ${router.searchViewName()}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("FILTER record.label == 'brainz'"))
    })

    test('cleans up possible array fields', async () => {
      class DB {
        public all (): any[] {
          return ['record']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      router = new RouterFuzzy(schemaConfig.protein)

      const page = 0
      await router.textSearch({ label: 'CTD' }, 'fuzzy', page)

      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`IN ${router.searchViewName()}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining('record[\'dbxrefs\']'))
    })
  })

  describe('generateRouter', () => {
    let routerBuilder: RouterFuzzy
    let router: routerType
    let openApi: any

    beforeEach(() => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const schemaConfig = loadSchemaConfig()

      routerBuilder = new RouterFuzzy(schemaConfig['cl class'])
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
