import { Router } from './routerFactory'
import { RouterFilterBy } from './routerFilterBy'
import { db } from '../../database'
import { configType } from '../../constants'
import { TRPCError } from '@trpc/server'
import { publicProcedure } from '../../trpc'
import { z } from 'zod'

export class RouterFilterByID extends RouterFilterBy implements Router {
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
      FILTER record._key == '${decodeURIComponent(id)}'
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
    const outputFormat = z.object(this.resolveTypes(this.output, true, false))

    return publicProcedure
      .meta({ openapi: { method: 'GET', path: `/${this.path}` } })
      .input(inputFormat)
      .output(outputFormat)
      .query(async ({ input }) => await this.getObjectById(input.id))
  }
}
