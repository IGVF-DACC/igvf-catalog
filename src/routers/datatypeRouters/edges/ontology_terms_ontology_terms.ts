import { z } from 'zod'
import { db } from '../../../database'
import { Edge, PathArangoDB, Paths, QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { descriptions } from '../descriptions'
import { ontologyFormat } from '../nodes/ontologies'
import { getDBReturnStatements, paramsFormatType } from '../_helpers'
import { commonNodesParamsFormat } from '../params'

const MAX_PAGE_SIZE = 500

const schema = loadSchemaConfig()

const edgeSchemaObj = schema['ontology relationship']
const ontologyTermSchema = schema['ontology term']

const ontologyRelativeFormat = z.object({
  term: ontologyFormat,
  relationship_type: z.string().nullable()
})

const ontologyRelativeQueryFormat = z.object({
  ontology_term_id: z.string().trim()
}).merge(commonNodesParamsFormat).omit({ organism: true })

const ontologyPathFormat = z.object({
  vertices: z.record(z.string(), z.object({
    uri: z.string(),
    term_id: z.string(),
    name: z.string(),
    synonyms: z.array(z.string()),
    description: z.string(),
    source: z.string(),
    subontology: z.string().nullish()
  })),
  paths: z.array(z.array(z.object({
    from: z.string(),
    to: z.string(),
    type: z.string()
  })))
})

async function getChildrenParents (input: paramsFormatType, opt: string): Promise<any[]> {
  const id = `${ontologyTermSchema.db_collection_name as string}/${decodeURIComponent(input.ontology_term_id as string)}`

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const query = `
    FOR record IN ${edgeSchemaObj.db_collection_name as string}
      LET details = (
        FOR otherRecord IN ${ontologyTermSchema.db_collection_name as string}
        FILTER otherRecord._id == record.${opt === 'children' ? '_from' : '_to'}
        RETURN {${getDBReturnStatements(ontologyTermSchema).replaceAll('record', 'otherRecord')}}
      )[0]

      FILTER record.${opt === 'children' ? '_to' : '_from'} == '${id}' && details != null && record.type == 'subclass'
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}

      RETURN {
        'term': details,
        'relationship_type': record.type || 'null'
      }
  `

  return await (await db.query(query)).all()
}

async function getPaths (from: string, to: string, fields: string[]): Promise<any> {
  const query = `
    FOR fromObj IN ${ontologyTermSchema.db_collection_name as string}
      FILTER fromObj._key == '${decodeURIComponent(from)}'

    FOR toObj IN ${ontologyTermSchema.db_collection_name as string}
      FILTER toObj._key == '${decodeURIComponent(to)}'

    FOR path IN ANY ALL_SHORTEST_PATHS
      fromObj TO toObj
      ${edgeSchemaObj.db_collection_name as string}
      RETURN path
  `

  const paths = await (await db.query(query)).all() as PathArangoDB[]

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

const ontologyTermChildren = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/ontology_terms/{ontology_term_id}/children', description: descriptions.ontology_terms_children } })
  .input(ontologyRelativeQueryFormat)
  .output(z.array(ontologyRelativeFormat.optional()))
  .query(async ({ input }) => await getChildrenParents(input, 'children'))

const ontologyTermParents = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/ontology_terms/{ontology_term_id}/parents', description: descriptions.ontology_terms_parents } })
  .input(ontologyRelativeQueryFormat)
  .output(z.array(ontologyRelativeFormat.optional()))
  .query(async ({ input }) => await getChildrenParents(input, 'parents'))

const ontologyTermTransitiveClosure = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/ontology_terms/{ontology_term_id_start}/transitive_closure/{ontology_term_id_end}', description: descriptions.ontology_terms_transitive_closure } })
  .input(z.object({ ontology_term_id_start: z.string().trim(), ontology_term_id_end: z.string().trim() }))
  .output(ontologyPathFormat)
  .query(async ({ input }) => await getPaths(input.ontology_term_id_start, input.ontology_term_id_end, Object.keys(ontologyFormat.shape)))

export const ontologyTermsEdgeRouters = {
  ontologyTermChildren,
  ontologyTermParents,
  ontologyTermTransitiveClosure
}
