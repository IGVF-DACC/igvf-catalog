import { z } from 'zod'
import { db } from '../database'
import { publicProcedure } from '../trpc'
import { TRPCError } from '@trpc/server'
import { configType, QUERY_LIMIT, PROPERTIES_TO_ZOD_MAPPING } from '../constants'

export interface Router {
  apiName: string
  hasGetByIDEndpoint: boolean
  generateRouter: () => any
}

class GeneralRouter implements Router {
  apiName: string
  apiSpecs: Record<string, string>
  properties: Record<string, string>
  filterBy: string[]
  filterByRange: string[]
  output: string[]
  hasGetByIDEndpoint: boolean
  dbCollectionName: string
  dbCollectionPerChromosome: boolean
  dbReturnStatements: string

  constructor (schemaObj: configType) {
    this.apiSpecs = schemaObj.accessible_via as Record<string, string>
    this.apiName = this.apiSpecs.name
    this.properties = schemaObj.properties as Record<string, string>
    this.filterBy = this.apiSpecs.filter_by.split(',').map((item: string) => item.trim())
    this.filterByRange = this.apiSpecs.filter_by_range.split(',').map((item: string) => item.trim())
    this.output = this.apiSpecs.return.split(',').map((item: string) => item.trim())
    this.hasGetByIDEndpoint = this.filterBy.includes('_id')
    this.dbCollectionName = schemaObj.db_collection_name as string

    // eslint-disable-next-line @typescript-eslint/strict-boolean-expressions
    this.dbCollectionPerChromosome = !!schemaObj.db_collection_per_chromosome

    const returns: string[] = []
    this.output.forEach((field: string) => {
      if (field === '_id') {
        returns.push('_id: record._key')
      } else if (this.properties[field] === 'int') {
        returns.push(`${field}: record['${field}:long']`)
      } else {
        returns.push(`'${field}': record['${field}']`)
      }
    })
    this.dbReturnStatements = returns.join(', ')
  }

  getFilterStatements (
    queryParams: Record<string, string | number | undefined>
  ): string {
    const dbFilterBy: string[] = []

    Object.keys(queryParams).forEach((element: string) => {
      if (queryParams[element] !== undefined) {
        if (this.filterByRange.includes(element)) {
          if (element === 'start') {
            dbFilterBy.push(`record['start:long'] >= ${queryParams[element] as number}`)
          } else if (element === 'end') {
            dbFilterBy.push(`record['end:long'] <= ${queryParams[element] as number}`)
          }
        } else {
          dbFilterBy.push(`record.${element} == '${queryParams[element] as string | number}'`)
        }
      }
    })

    if (dbFilterBy.length === 0) {
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: 'At least one parameter must be defined.'
      })
    }

    return dbFilterBy.join(' and ')
  }

  async getObjects (
    queryParams: Record<string, string | number | undefined>
  ): Promise<any[]> {
    let collectionName = this.dbCollectionName
    if (this.dbCollectionPerChromosome) {
      collectionName = `${this.dbCollectionName}_${queryParams.chr as string}`
    }

    let page = 0
    if (Object.hasOwn(queryParams, 'page')) {
      page = parseInt(queryParams.page as string)
    }

    const query = `
      FOR record IN ${collectionName}
      FILTER ${this.getFilterStatements(queryParams)}
      LIMIT ${page}, ${QUERY_LIMIT}
      RETURN { ${this.dbReturnStatements} }
    `

    console.log(query)
    const cursor = await db.query(query)
    return await cursor.all()
  }

  resolveTypes (params: string[], addID: boolean): z.ZodType {
    const paramTypes: Record<string, z.ZodType> = {}

    params.filter(p => addID || p !== '_id').forEach((param: string) => {
      paramTypes[param] = PROPERTIES_TO_ZOD_MAPPING[this.properties[param]] ?? z.string().optional()
    })

    return z.object(paramTypes)
  }

  generateRouter (): any {
    const path = `/${this.apiName}` as const
    const inputFormat = this.resolveTypes([...this.filterBy, ...this.filterByRange], false)
    const outputFormat = z.array(this.resolveTypes(this.output, true))

    return publicProcedure
      .meta({ openapi: { method: 'GET', path, description: this.apiSpecs.description } })
      .input(inputFormat)
      .output(outputFormat)
      .query(async ({ input }) => await this.getObjects(input))
  }
}

class GeneralRouterID extends GeneralRouter implements Router {
  path: string
  hasGetByIDEndpoint = false

  constructor (schemaObj: configType) {
    super(schemaObj)

    this.path = `${this.apiName}/{id}`
    this.apiName = this.apiName + '_id'
  }

  async getObjectById (id: string): Promise<any[]> {
    const query = `
      FOR record IN ${this.dbCollectionName}
      FILTER record._key == '${id}'
      RETURN { ${this.dbReturnStatements} }
    `
    const cursor = await db.query(query)
    const record = (await cursor.all())[0]

    if (record === undefined) {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: `Record ${id} not found.`
      })
    }

    return record
  }

  generateRouter (): any {
    const inputFormat = z.object({ id: z.string() })
    const outputFormat = this.resolveTypes(this.output, true)

    return publicProcedure
      .meta({ openapi: { method: 'GET', path: `/${this.path}` } })
      .input(inputFormat)
      .output(outputFormat)
      .query(async ({ input }) => await this.getObjectById(input.id))
  }
}

// eslint-disable-next-line @typescript-eslint/no-extraneous-class
export class RouterFactory {
  static create (schemaObj: configType, routerType: string = 'default'): Router {
    if (routerType === 'id') {
      return new GeneralRouterID(schemaObj)
    }

    return new GeneralRouter(schemaObj)
  }
}
