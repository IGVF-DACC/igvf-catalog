import mock = require('mock-fs')
import { parse } from 'yaml'
import { schemaConfigFilePath } from '../../../constants'
import { generateRouters, getActiveNodes, getActiveEdges, loadSchemaConfig, readRelationships } from '../../genericRouters/genericRouters'

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
    fuzzy_text_search: chr
    filter_by: _id, chr, pos
    return: _id, chr, pos
  properties:
    chr: str
    pos: int

open chromatin region:
  represented_as: node
  db_collection_name: open_chromatin_regions
  db_collection_per_chromosome: false
  accessible_via:
    name: open_chromatin_regions
    description: 'Retrieve variants data. Example: chr = chr1'
    filter_by: chr, pos
    return: _id, chr, pos
  properties:
    chr: str
    pos: int
`

const SCHEMA_CONFIG_NO_RELATIONSHIPS_NO_ENDPOINTS = `
topld:
  represented_as: edge
  inherit_properties: true
  label_in_input: topld
  label_as_edge: VARIANT_CORRELATION
  db_collection_name: variant_correlations
  db_collection_per_chromosome: false
  properties:
    chr: str
    ancestry: str

sequence variant:
  represented_as: node
  label_in_input: gnomad
  db_collection_name: variants
  db_collection_per_chromosome: false
  properties:
    chr: str
    pos: int
`

describe('Generic Routers', () => {
  afterEach(() => {
    mock.restore()
  })

  describe('loadSchemaConfig', () => {
    test('loads configuration from yaml config file', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      expect(loadSchemaConfig()).toEqual(parse(SCHEMA_CONFIG))
    })
  })

  describe('getActiveNodes', () => {
    test('returns list of all nodes containing an accessible_via field in their config', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const response = new Set()
      response.add('sequence variant')
      response.add('open chromatin region')
      expect(getActiveNodes(loadSchemaConfig())).toEqual(response)
    })

    test('returns empty list if no nodes have accessible_via field in their config', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG_NO_RELATIONSHIPS_NO_ENDPOINTS
      mock(config)

      const response = new Set()
      expect(getActiveNodes(loadSchemaConfig())).toEqual(response)
    })
  })

  describe('getActiveEdges', () => {
    test('returns list of all edges with active nodes', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const response = new Set()
      response.add('variant to variant correlation')
      expect(getActiveEdges(loadSchemaConfig())).toEqual(response)
    })

    test('returns empty list if edges have no nodes with accessible_via field in their config', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG_NO_RELATIONSHIPS_NO_ENDPOINTS
      mock(config)

      const response = new Set()
      expect(getActiveEdges(loadSchemaConfig())).toEqual(response)
    })
  })

  describe('readRelationships', () => {
    test('returns empty relationships if schema is not part of any relationships', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const emptyRelationships = {
        parents: [],
        children: []
      }
      expect(readRelationships(loadSchemaConfig(), 'inexistent type')).toEqual(emptyRelationships)
    })

    test('returns empty relationships if schema has no relationships defined', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG_NO_RELATIONSHIPS_NO_ENDPOINTS
      mock(config)

      const emptyRelationships = {
        parents: [],
        children: []
      }
      expect(readRelationships(loadSchemaConfig(), 'sequence variant')).toEqual(emptyRelationships)
    })

    test('returns relationships DB collections if defined', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const relationships = {
        parents: ['variant_correlations'],
        children: ['variant_correlations']
      }
      expect(readRelationships(loadSchemaConfig(), 'sequence variant')).toEqual(relationships)
    })
  })

  describe('generateRouters', () => {
    test('does not generate routers if no API is defined by accessed_via', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG_NO_RELATIONSHIPS_NO_ENDPOINTS
      mock(config)

      expect(generateRouters()).toEqual({})
    })

    test('generates basic routers if API is defined by accessed_via', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const routers = Object.keys(generateRouters())
      expect(routers).toContain('variants')
      expect(routers).not.toContain('variant_correlations')
    })

    test('generates get by ID endpoint if API returns id field', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const routers = Object.keys(generateRouters())
      expect(routers).toContain('variants')
      expect(routers).toContain('variants_id')
      expect(routers).toContain('open_chromatin_regions')
      expect(routers).not.toContain('open_chromatin_regions_id')
    })

    test('generates graph endpoints if API returns id field', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const routers = Object.keys(generateRouters())
      expect(routers).toContain('variants_children')
      expect(routers).toContain('variants_parents')
      expect(routers).not.toContain('open_chromatin_regions_children')
      expect(routers).not.toContain('open_chromatin_regions_parents')
    })

    test('generates fuzzy text search endpoint if API contains fuzzy_text_search key', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const routers = Object.keys(generateRouters())
      expect(routers).toContain('variants_search')
    })

    test('generates transitive closure endpoint if API contains active edges', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const routers = Object.keys(generateRouters())
      expect(routers).toContain('topld/transitiveClosure')
    })
  })
})
