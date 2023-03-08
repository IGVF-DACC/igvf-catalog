import { RouterFilterBy } from './routerFilterBy'
import { RouterGraph } from './routerGraph'
import { RouterFilterByID } from './routerFilterByID'
import { configType } from '../../constants'

export interface Router {
  apiName: string
  hasGetByIDEndpoint: boolean
  generateRouter: (opts?: any) => any
}

export class RouterFactory {
  static create (schemaObj: configType, routerType: string = 'default', opts: any = null): Router {
    if (routerType === 'id') {
      return new RouterFilterByID(schemaObj)
    } else if (routerType === 'graph') {
      return new RouterGraph(schemaObj, opts)
    }

    return new RouterFilterBy(schemaObj)
  }
}
