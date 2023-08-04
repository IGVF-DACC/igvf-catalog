import { RouterFilterBy } from './routerFilterBy'
import { loadSchemaConfig } from './genericRouters'
import { db } from '../../database'
import { configType, QUERY_LIMIT } from '../../constants'
import { paramsFormatType, preProcessRegionParam } from '../datatypeRouters/_helpers'

export class RouterEdges {
  edgeCollection: string
  secondaryEdgeCollection: string | undefined
  secondaryRouter: RouterEdges | undefined
  sourceSchemaCollection: string
  targetSchemaCollection: string
  sourceReturnStatements: string
  targetReturnStatements: string
  sourceSchema: Record<string, string>
  targetSchema: Record<string, string>

  constructor (schemaObj: configType, secondaryRouter: RouterEdges | undefined = undefined) {
    this.secondaryRouter = secondaryRouter

    this.edgeCollection = schemaObj.db_collection_name as string
    this.secondaryEdgeCollection = secondaryRouter?.edgeCollection as string

    const schema = loadSchemaConfig()

    const edge = schemaObj.relationship as Record<string, string>
    const sourceSchemaName = edge.from
    const targetSchemaName = edge.to

    this.sourceSchema = schema[sourceSchemaName] as Record<string, string>
    this.targetSchema = schema[targetSchemaName] as Record<string, string>

    this.sourceReturnStatements = (new RouterFilterBy(this.sourceSchema)).dbReturnStatements
    this.targetReturnStatements = (new RouterFilterBy(this.targetSchema)).dbReturnStatements

    this.sourceSchemaCollection = this.sourceSchema.db_collection_name
    this.targetSchemaCollection = this.targetSchema.db_collection_name
  }

  filterStatements (input: paramsFormatType, querySchema: Record<string, string>): string {
    const preProcessed = preProcessRegionParam(input)
    const router = new RouterFilterBy(querySchema)
    return router.getFilterStatements(preProcessed)
  }

  sortByStatement (sortBy: string): string {
    return sortBy !== '' || sortBy !== undefined ? `SORT record['${sortBy}']` : ''
  }

  // A -> B => given ID for A, return B
  async getTargetsByID (sourceId: string, page: number = 0, sortBy: string = ''): Promise<any[]> {
    const query = `
      LET targets = (
        FOR record IN ${this.edgeCollection}
        FILTER record._from == '${this.sourceSchemaCollection}/${decodeURIComponent(sourceId)}'
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN DOCUMENT(record._to)
      )

      FOR record in targets
        RETURN { ${this.targetReturnStatements} }
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A -> B => given a query for A, return B
  async getTargets (input: paramsFormatType, sortBy: string = ''): Promise<any[]> {
    const page = input.page as number

    const query = `
      LET sources = (
        FOR record in ${this.sourceSchemaCollection}
        FILTER ${this.filterStatements(input, this.sourceSchema)}
        RETURN record._id
      )

      LET targets = (
          FOR record IN ${this.edgeCollection}
            FILTER record._from IN sources
            ${this.sortByStatement(sortBy)}
            LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
            RETURN DOCUMENT(record._to)
      )

      FOR record in targets
        RETURN { ${this.targetReturnStatements} }
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A -> B => given ID for B, return A
  async getSourcesByID (targetId: string, page: number = 0, sortBy: string = ''): Promise<any[]> {
    const query = `
      LET sources = (
        FOR record IN ${this.edgeCollection}
        FILTER record._to == '${this.targetSchemaCollection}/${decodeURIComponent(targetId)}'
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN DOCUMENT(record._from)
      )

      FOR record in sources
        RETURN { ${this.sourceReturnStatements} }
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A -> B => given a query for B, return A
  async getSources (input: paramsFormatType, sortBy: string = ''): Promise<any[]> {
    const page = input.page as number

    const query = `
      LET targets = (
        FOR record in ${this.targetSchemaCollection}
        FILTER ${this.filterStatements(input, this.targetSchema)}
        RETURN record._id
      )

      LET sources = (
          FOR record IN ${this.edgeCollection}
            FILTER record._to IN targets
            ${this.sortByStatement(sortBy)}
            LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
            RETURN DOCUMENT(record._to)
      )

      FOR record in sources
        RETURN { ${this.sourceReturnStatements} }
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A -> B, B -> C => given ID for A, return C
  async getSecondaryTargetsByID (sourceId: string, page: number = 0, sortBy: string = ''): Promise<any[]> {
    const query = `
      LET primaryTargets = (
        FOR record IN ${this.edgeCollection}
        FILTER record._from == '${this.sourceSchemaCollection}/${decodeURIComponent(sourceId)}'
        RETURN record._to
      )

      LET secondaryTargets = (
        FOR record in ${this.secondaryEdgeCollection as string}
        FILTER record._from in primaryTargets
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN DOCUMENT(record._to)
      )

      FOR record in secondaryTargets
        RETURN {${this.secondaryRouter?.targetReturnStatements as string}}
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A -> B, B -> C => given a query for A, return C
  async getSecondaryTargets (input: paramsFormatType, sortBy: string = ''): Promise<any[]> {
    const page = input.page as number

    const query = `
      LET primaryTargets = (
        FOR record IN ${this.sourceSchemaCollection}
        FILTER ${this.filterStatements(input, this.sourceSchema)}
        RETURN record._id
      )

      LET secondarySources = (
        FOR record IN ${this.edgeCollection}
        FILTER record._from IN primaryTargets
        RETURN record._to
      )

      LET secondaryTargets = (
        FOR record in ${this.secondaryEdgeCollection as string}
        FILTER record._from IN secondarySources
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN DOCUMENT(record._to)
      )

      FOR record in secondaryTargets
        RETURN {${this.secondaryRouter?.targetReturnStatements as string}}
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A -> B, B -> C => given ID for C, return A
  async getSecondarySourcesByID (targetId: string, page: number = 0, sortBy: string = ''): Promise<any[]> {
    // C
    const secondaryTargetCollection = this.secondaryRouter?.targetSchemaCollection as string

    const query = `
      LET secondarySources = (
        FOR record IN ${this.secondaryEdgeCollection as string}
        FILTER record._to == '${secondaryTargetCollection}/${decodeURIComponent(targetId)}'
        RETURN record._from
      )

      LET primarySources = (
        FOR record in ${this.edgeCollection}
        FILTER record._to in secondarySources
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN DOCUMENT(record._from)
      )

      FOR record in primarySources
        RETURN {${this.sourceReturnStatements}}
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A -> B, B -> C => given a query for C, return A
  async getSecondarySources (input: paramsFormatType, sortBy: string = ''): Promise<any[]> {
    const page = input.page as number

    const query = `
      LET secondaryTargets = (
        FOR record IN ${this.secondaryRouter?.targetSchemaCollection as string}
        FILTER ${this.filterStatements(input, this.secondaryRouter?.targetSchema as Record<string, string>)}
        RETURN record._id
      )

      LET secondarySources = (
        FOR record in ${this.secondaryEdgeCollection as string}
        FILTER record._to IN secondaryTargets
        RETURN record._from
      )

      LET primarySources = (
        FOR record in ${this.edgeCollection}
        FILTER record._to in secondarySources
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN DOCUMENT(record._from)
      )

      FOR record in primarySources
        RETURN {${this.sourceReturnStatements}}
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }
}
