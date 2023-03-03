import { Router } from './routerFactory'
import { RouterFilterBy } from './routerFilterBy'
import { db } from '../../database'
import { configType } from '../../constants'
import { publicProcedure } from '../../trpc'
import { z } from 'zod'

export class RouterGraph extends RouterFilterBy implements Router {
  path: string
  relationshipCollections: string[]
  hasGetByIDEndpoint = false

  constructor (schemaObj: configType, relationshipCollections: string[]) {
    super(schemaObj)

    this.relationshipCollections = relationshipCollections
    this.path = `${this.apiName}/{id}`
  }

  async getObjectByGraphQuery (id: string, opt: string): Promise<any[]> {
    const letQueries: string[] = []
    let count = 1
    this.relationshipCollections.forEach(collection => {
      letQueries.push(` LET q${count} = (
        FOR record IN ${collection}
        FILTER record.${opt === 'children' ? '_from' : '_to'} == '${id}'
        RETURN record.${opt === 'children' ? '_to' : '_from'}
      )`)
      count += 1
    })
    count -= 1

    const union = []
    while (count > 0) {
      union.push(`q${count}`)
      count -= 1
    }

    const query = letQueries.join('\n') + `\nRETURN union(${union.join(',')})`

    const cursor = await db.query(query)
    const record = (await cursor.all())[0]

    console.log(await cursor.all())

    return record
  }

  generateRouter (opt?: string | undefined): any {
    const inputFormat = z.object({ id: z.string() })
    const outputFormat = z.array(z.string())

    let path = this.path
    if (opt === 'children' || opt === 'parents') {
      path += `/${opt}`
    }

    return publicProcedure
      .meta({ openapi: { method: 'GET', path: `/${path}` } })
      .input(inputFormat)
      .output(outputFormat)
      .query(async ({ input }) => await this.getObjectByGraphQuery(decodeURIComponent(input.id), opt as string))
  }
}
