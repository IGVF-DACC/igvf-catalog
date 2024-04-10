import { Router } from './routerFactory'
import { db } from '../../database'
import { configType, PathArangoDB } from '../../constants'
import { publicProcedure } from '../../trpc'
import { z } from 'zod'

const edgeSchema = z.object({
  to: z.string(),
  from: z.string(),
  type: z.string()
})
type Edge = z.infer<typeof edgeSchema>

const pathsSchema = z.object({
  vertices: z.record(z.string(), z.any()),
  paths: z.array(z.array(edgeSchema))
})
type Paths = z.infer<typeof pathsSchema>

export class RouterTransitiveClosure implements Router {
  apiName: string
  path: string
  edgeDBCollectionName: string
  hasGetByIDEndpoint: boolean = false
  fuzzyTextSearch: string[] = []
  nodeCollectioName: string

  constructor (schemaObj: configType, nodeCollectionName: string = '') {
    this.apiName = `${schemaObj.label_in_input as string}/transitiveClosure`
    this.path = `${this.apiName}/{from}/{to}`
    this.edgeDBCollectionName = schemaObj.db_collection_name as string
    this.nodeCollectioName = nodeCollectionName
  }

  // A --(edge1)-> A1 ... -> BN --(edgeN) --> B, given A and B, returns all possible [edge1, ..., edgeN]
  // and all [A1, ... BN] nodes and their properties specified by the parameter: `fields`.
  async getPaths (from: string, to: string, fields: string[]): Promise<any> {
    const query = `
    FOR fromObj IN ${this.nodeCollectioName}
      FILTER fromObj._key == '${decodeURIComponent(from)}'
    FOR toObj IN ${this.nodeCollectioName}
      FILTER toObj._key == '${decodeURIComponent(to)}'
    FOR path IN ANY ALL_SHORTEST_PATHS
      fromObj TO toObj
      ${this.edgeDBCollectionName}
      RETURN path
    `

    const cursor = await db.query(query)
    const paths = await cursor.all() as PathArangoDB[]

    const totalVertices: Record<string, any> = {}
    const edgesPaths: Edge[][] = []

    paths.forEach(path => {
      path.vertices.forEach(vertix => {
        const filteredObject: Record<string, any> = {}
        fields.forEach((key) => {
          filteredObject[key] = vertix[key]
        })

        totalVertices[vertix._key] = filteredObject
      })
      const edges: Edge[] = []
      path.edges.forEach(edge => {
        edges.push({
          from: edge._from.split('/')[1],
          to: edge._to.split('/')[1],
          type: edge.type
        })
      })
      edgesPaths.push(edges)
    })

    const returnValue: Paths = {
      vertices: totalVertices,
      paths: edgesPaths
    }

    return returnValue
  }

  generateRouter (): any {
    const inputFormat = z.object({
      from: z.string().trim(),
      to: z.string().trim()
    })

    return publicProcedure
      .meta({ openapi: { method: 'GET', path: `/${this.path}` } })
      .input(inputFormat)
      .output(pathsSchema)
      .query(async ({ input }) => await this.getPaths(input.from, input.to, ['_key']))
  }
}
