import mock = require('mock-fs')
import { schemaConfigFilePath } from '../../../constants'
import { RouterFactory } from '../../genericRouters/routerFactory'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { RouterFilterByID } from '../../genericRouters/routerFilterByID'
import { RouterFuzzy } from '../../genericRouters/routerFuzzy'
import { RouterTransitiveClosure } from '../../genericRouters/routerTransitiveClosure'

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

describe('routerFactory', () => {
  afterEach(() => {
    mock.restore()
  })

  describe('Router Factory constructor', () => {
    test('it creates default Filter By routers', () => {
      const config: Record<string, string> = {}
      config[schemaConfigFilePath] = SCHEMA_CONFIG
      mock(config)

      const schemaConfig = loadSchemaConfig()['sequence variant']

      expect(RouterFactory.create(schemaConfig)).toBeInstanceOf(RouterFilterBy)
      expect(RouterFactory.create(schemaConfig, 'id')).toBeInstanceOf(RouterFilterByID)
      expect(RouterFactory.create(schemaConfig, 'fuzzy')).toBeInstanceOf(RouterFuzzy)
      expect(RouterFactory.create(schemaConfig, 'transitiveClosure')).toBeInstanceOf(RouterTransitiveClosure)
    })
  })
})
