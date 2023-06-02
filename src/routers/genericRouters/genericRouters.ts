import { parse } from 'yaml'
import * as fs from 'fs'

import { RouterFactory, Router } from './routerFactory'
import { publicProcedure } from '../../trpc'
import { schemaConfigFilePath } from '../../constants'

type configType = Record<string, string | Record<string, string>>
type routerType = typeof publicProcedure

export function loadSchemaConfig (): Record<string, configType> {
  return parse(fs.readFileSync(schemaConfigFilePath, 'utf8'))
}

// Active nodes are the ones which contain an `accessible_via` block
export function getActiveNodes (schemaConfig: Record<string, configType>): Set<string> {
  const nodes = new Set<string>()

  Object.keys(schemaConfig).forEach(schema => {
    if (Object.hasOwn(schemaConfig[schema], 'accessible_via')) {
      nodes.add(schema)
    }
  })
  return nodes
}

// Active edges are the ones which contains only active nodes
export function getActiveEdges (schemaConfig: Record<string, configType>): Set<string> {
  const nodes = getActiveNodes(schemaConfig)
  const edges = new Set<string>()

  Object.keys(schemaConfig).forEach(schema => {
    if (Object.hasOwn(schemaConfig[schema], 'relationship')) {
      const schemaRelationships = schemaConfig[schema].relationship as Record<string, string>

      if (nodes.has(schemaRelationships.to) && nodes.has(schemaRelationships.from)) {
        edges.add(schema)
      }
    }
  })

  return edges
}

export function readRelationships (schemaConfig: Record<string, configType>, schemaName: string): Record<string, string[]> {
  const relationships: Record<string, string[]> = {
    parents: [],
    children: []
  }

  Object.keys(schemaConfig).forEach(schema => {
    if (Object.hasOwn(schemaConfig[schema], 'relationship')) {
      const schemaRelationships = schemaConfig[schema].relationship as Record<string, string>
      const edgeDBCollectionName = schemaConfig[schema].db_collection_name as string

      if (schemaRelationships.to === schemaName) {
        relationships.parents.push(edgeDBCollectionName)
      }

      if (schemaRelationships.from === schemaName) {
        relationships.children.push(edgeDBCollectionName)
      }
    }
  })

  return relationships
}

export function generateRouters (): Record<string, routerType> {
  const routers: Record<string, routerType> = {}

  const schemaConfig = loadSchemaConfig()

  const activeEdges = getActiveEdges(schemaConfig)
  Object.keys(schemaConfig).forEach(schema => {
    const schemaObj = schemaConfig[schema]

    if (schemaObj.represented_as === 'edge' && activeEdges.has(schema)) {
      const router = RouterFactory.create(schemaObj, 'transitiveClosure')
      routers[router.apiName] = router.generateRouter()
    }

    if (Object.hasOwn(schemaObj, 'accessible_via')) {
      let router: Router = RouterFactory.create(schemaObj)
      routers[router.apiName] = router.generateRouter()

      if (router.hasGetByIDEndpoint) {
        router = RouterFactory.create(schemaObj, 'id')
        routers[router.apiName] = router.generateRouter()
      }

      const relationships = readRelationships(schemaConfig, schema)
      if (relationships.children.length > 0) {
        router = RouterFactory.create(schemaObj, 'graph', relationships.children)
        routers[router.apiName + '_children'] = router.generateRouter('children')
      }
      if (relationships.parents.length > 0) {
        router = RouterFactory.create(schemaObj, 'graph', relationships.parents)
        routers[router.apiName + '_parents'] = router.generateRouter('parents')
      }

      if (router.fuzzyTextSearch.length > 0) {
        router = RouterFactory.create(schemaObj, 'fuzzy')
        routers[router.apiName + '_search'] = router.generateRouter()
      }
    }
  })

  return routers
}

export const genericRouters = generateRouters()
