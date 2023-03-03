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

export function readRelationships (schemaConfig: Record<string, configType>, schemaName: string): Record<string, string[]> {
  const relationships: Record<string, string[]> = {
    parents: [],
    children: []
  }

  Object.keys(schemaConfig).forEach(schema => {
    if (Object.hasOwn(schemaConfig[schema], 'relationship')) {
      const schemaRelationships = schemaConfig[schema].relationship as Record<string, string>
      const dbCollectionName = schemaConfig[schema].db_collection_name as string

      if (schemaRelationships.to === schemaName) {
        relationships.parents.push(dbCollectionName)
      }

      if (schemaRelationships.from === schemaName) {
        relationships.children.push(dbCollectionName)
      }
    }
  })

  return relationships
}

export function generateRouters (): Record<string, routerType> {
  const routers: Record<string, routerType> = {}

  const schemaConfig = loadSchemaConfig()

  Object.keys(schemaConfig).forEach(schema => {
    if (Object.hasOwn(schemaConfig[schema], 'accessible_via')) {
      const schemaObj = schemaConfig[schema]

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
    }
  })

  return routers
}

export const genericRouters = generateRouters()
