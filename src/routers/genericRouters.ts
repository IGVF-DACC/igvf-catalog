import { RouterFactory, Router } from './_routerGenerator'
import { SCHEMA_CONFIG, routerType } from '../constants'

export function generateRouters (): Record<string, routerType> {
  const routers: Record<string, routerType> = {}

  Object.keys(SCHEMA_CONFIG).forEach(schema => {
    if (Object.hasOwn(SCHEMA_CONFIG[schema], 'accessible_via')) {
      const schemaObj = SCHEMA_CONFIG[schema]

      let router: Router = RouterFactory.create(schemaObj)
      routers[router.apiName] = router.generateRouter()

      if (router.hasGetByIDEndpoint) {
        router = RouterFactory.create(schemaObj, 'id')
        routers[router.apiName] = router.generateRouter()
      }
    }
  })

  return routers
}

export const genericRouters = generateRouters()
