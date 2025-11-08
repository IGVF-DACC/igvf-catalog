import { vol } from 'memfs'
import { parse } from 'yaml'
import { schemaConfigFilePath } from '../../../constants'
import { getActiveNodes, getActiveEdges, loadSchemaConfig, readRelationships } from '../../genericRouters/genericRouters'

// Mock fs to use memfs
jest.mock('fs', () => require('memfs').fs)
jest.mock('fs/promises', () => require('memfs').fs.promises)

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
    vol.reset()
  })

  describe('loadSchemaConfig', () => {
    test('loads configuration from yaml config file', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      vol.fromJSON(config)

      expect(loadSchemaConfig()).toEqual(parse(SCHEMA_CONFIG))
    })
  })

  describe('getActiveNodes', () => {
    test('returns list of all nodes containing an accessible_via field in their config', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      vol.fromJSON(config)

      const response = new Set()
      response.add('sequence variant')
      response.add('open chromatin region')
      expect(getActiveNodes(loadSchemaConfig())).toEqual(response)
    })

    test('returns empty list if no nodes have accessible_via field in their config', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG_NO_RELATIONSHIPS_NO_ENDPOINTS
      vol.fromJSON(config)

      const response = new Set()
      expect(getActiveNodes(loadSchemaConfig())).toEqual(response)
    })
  })

  describe('getActiveEdges', () => {
    test('returns list of all edges with active nodes', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      vol.fromJSON(config)

      const response = new Set()
      response.add('variant to variant correlation')
      expect(getActiveEdges(loadSchemaConfig())).toEqual(response)
    })

    test('returns empty list if edges have no nodes with accessible_via field in their config', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG_NO_RELATIONSHIPS_NO_ENDPOINTS
      vol.fromJSON(config)

      const response = new Set()
      expect(getActiveEdges(loadSchemaConfig())).toEqual(response)
    })
  })

  describe('readRelationships', () => {
    test('returns empty relationships if schema is not part of any relationships', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      vol.fromJSON(config)

      const emptyRelationships = {
        parents: [],
        children: []
      }
      expect(readRelationships(loadSchemaConfig(), 'inexistent type')).toEqual(emptyRelationships)
    })

    test('returns empty relationships if schema has no relationships defined', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG_NO_RELATIONSHIPS_NO_ENDPOINTS
      vol.fromJSON(config)

      const emptyRelationships = {
        parents: [],
        children: []
      }
      expect(readRelationships(loadSchemaConfig(), 'sequence variant')).toEqual(emptyRelationships)
    })

    test('returns relationships DB collections if defined', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      vol.fromJSON(config)

      const relationships = {
        parents: ['variant_correlations'],
        children: ['variant_correlations']
      }
      expect(readRelationships(loadSchemaConfig(), 'sequence variant')).toEqual(relationships)
    })
  })
})
