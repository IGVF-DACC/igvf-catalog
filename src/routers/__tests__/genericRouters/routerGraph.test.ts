import mock = require('mock-fs')
import { db } from '../../../database'
import { configType, schemaConfigFilePath } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig, readRelationships } from '../../genericRouters/genericRouters'
import { RouterGraph } from '../../genericRouters/routerGraph'

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

accessible dna region:
  represented_as: node
  label_in_input: accessible_dna_region
  db_collection_name: accessible_dna_regions
  db_collection_per_chromosome: false
  db_indexes:
    coordinates:
      type: zkd
      fields: start:long,end:long
  accessible_via:
    name: accessible_dna_regions
    description: 'Retrieve accessible dna regions data. Example: chr = chr1'
    filter_by: _id, chr
    filter_by_range: start, end
    return: _id, chr, start, end
  properties:
    chr: str
    start: int
    end: int
  aliases: [ 'dnase-seq accessible region', 'atac-seq accessible region' ]
  description: >-
    A region (or regions) of a chromatinized genome that has been measured to be more
    accessible to an enzyme such as DNase-I or Tn5 Transpose
  is_a: regulatory region
  mixins:
    - genomic entity
    - chemical entity or gene or gene product
    - physical essence
    - ontology class
  exact_mappings:
    - SO:0002231


caqtl:
  represented_as: edge
  label_in_input: caqtl
  label_as_edge: VARIANT_ACCESSIBLE_DNA_REGION
  db_collection_name: variant_accessible_dna_region_links
  db_collection_per_chromosome: false
  relationship:
    from: sequence variant
    to: accessible dna region
  properties:
    chr: str
    rsid: str
`

describe('routerGraph', () => {
  afterEach(() => {
    mock.restore()
  })

  describe('constructor', () => {
    test('it parses config fields accordingly', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const schemaConfig = loadSchemaConfig()
      const relationships = readRelationships(schemaConfig, 'sequence variant')

      const router = new RouterGraph(schemaConfig['sequence variant'], relationships.parents)

      expect(router.apiName).toEqual('variants')
      expect(router.path).toEqual('variants/{id}')
      expect(router.relationshipCollections).toEqual(relationships.parents)
      expect(router.apiSpecs).toEqual({
        name: 'variants',
        description: 'Retrieve variants data. Example: chr = chr1',
        filter_by: '_id, chr, pos',
        return: '_id, chr, pos'
      })
      expect(router.properties).toEqual({
        chr: 'str',
        pos: 'int'
      })
      expect(router.filterBy).toEqual(['_id', 'chr', 'pos'])
      expect(router.output).toEqual(['_id', 'chr', 'pos'])
      expect(router.hasGetByIDEndpoint).toEqual(false)
      expect(router.dbCollectionName).toEqual('variants')
      expect(router.dbCollectionPerChromosome).toEqual(false)
      expect(router.dbReturnStatements).toEqual("_id: record._key, 'chr': record['chr'], pos: record['pos:long']")
    })
  })

  describe('getObjectByGraphQuery', () => {
    let router: RouterGraph
    let relationships: Record<string, string[]>
    let schemaConfig: Record<string, configType>

    beforeEach(() => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      schemaConfig = loadSchemaConfig()
    })

    test('queries correct DB collection and return parent records', async () => {
      class DB {
        public all (): any[] {
          return ['record']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      relationships = readRelationships(schemaConfig, 'sequence variant')
      router = new RouterGraph(schemaConfig['sequence variant'], relationships.parents)

      const relationshipType = 'variant_correlations'
      const records = await router.getObjectByGraphQuery('random_variant_id', relationshipType, 'parent')
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`FOR record IN ${relationshipType}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("record._to == 'variants/random_variant_id'"))

      expect(records).toEqual(['record'])
    })

    test('queries correct DB collection and return child records', async () => {
      class DB {
        public all (): any[] {
          return ['record']
        }
      }

      const mockPromise = new Promise<any>((resolve) => {
        resolve(new DB())
      })
      const mockQuery = jest.spyOn(db, 'query').mockReturnValue(mockPromise)

      relationships = readRelationships(schemaConfig, 'sequence variant')

      router = new RouterGraph(schemaConfig['sequence variant'], relationships.children)

      const relationshipType = 'variant_accessible_dna_region_links'
      const records = await router.getObjectByGraphQuery('random_variant_id', relationshipType, 'children')
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining(`FOR record IN ${relationshipType}`))
      expect(mockQuery).toHaveBeenCalledWith(expect.stringContaining("record._from == 'variants/random_variant_id'"))

      expect(records).toEqual(['record'])
    })
  })

  describe('generateRouter', () => {
    let routerBuilder: RouterGraph
    let router: routerType
    let openApi: any

    beforeEach(() => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const schemaConfig = loadSchemaConfig()
      const relationships = readRelationships(schemaConfig, 'sequence variant')

      routerBuilder = new RouterGraph(schemaConfig['sequence variant'], relationships.parents)
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
