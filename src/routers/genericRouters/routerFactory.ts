import { RouterFilterBy } from './routerFilterBy'
import { RouterGraph } from './routerGraph'
import { RouterFilterByID } from './routerFilterByID'
import { RouterFuzzy } from './routerFuzzy'
import { configType } from '../../constants'
import { RouterTransitiveClosure } from './routerTransitiveClosure'

export interface Router {
  apiName: string
  hasGetByIDEndpoint: boolean
  fuzzyTextSearch: string[]
  generateRouter: (opts?: any) => any
}

export class RouterFactory {
  static create (schemaObj: configType, routerType: string = 'default', opts: any = null): Router {
    if (routerType === 'id') {
      return new RouterFilterByID(schemaObj)
    } else if (routerType === 'graph') {
      return new RouterGraph(schemaObj, opts)
    } else if (routerType === 'fuzzy') {
      return new RouterFuzzy(schemaObj)
    } else if (routerType === 'transitiveClosure') {
      return new RouterTransitiveClosure(schemaObj)
    }

    return new RouterFilterBy(schemaObj)
  }
}
