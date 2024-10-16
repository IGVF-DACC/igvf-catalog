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
  nodeCollection: string

  constructor (schemaObj: configType, relationshipCollections: string[] = []) {
    super(schemaObj)

    this.nodeCollection = schemaObj.db_collection_name as string
    this.relationshipCollections = relationshipCollections
    this.path = `${this.apiName}/{id}`
  }

  async getObjectByGraphQuery (id: string, relationshipType: string, opt: string): Promise<any[]> {
    const query = `FOR record IN ${relationshipType}
      FILTER record.${opt === 'children' ? '_from' : '_to'} == '${this.nodeCollection}/${decodeURIComponent(id)}'
      RETURN DISTINCT({'ontology_term_id': SPLIT(record.${opt === 'children' ? '_to' : '_from'}, '/')[1], 'relationship_type': record.type || 'null'})`

    const cursor = await db.query(query)
    const record = await cursor.all()

    return record
  }

  generateRouter (opt?: string | undefined): any {
    const outputFormat = z.array(z.array(z.string(), z.string().nullable().optional()).optional())
    const inputFormat = z.object({ id: z.string().trim(), relationship_type: z.enum(['', ...this.relationshipCollections]) })

    let path = this.path
    if (opt === 'children' || opt === 'parents') {
      path += `/${opt}`
    }

    return publicProcedure
      .meta({ openapi: { method: 'GET', path: `/${path}` } })
      .input(inputFormat)
      .output(outputFormat)
      .query(async ({ input }) => await this.getObjectByGraphQuery(input.id, input.relationship_type, opt as string))
  }
}
