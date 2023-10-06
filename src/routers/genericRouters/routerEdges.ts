import { RouterFilterBy } from './routerFilterBy'
import { loadSchemaConfig } from './genericRouters'
import { db } from '../../database'
import { configType, QUERY_LIMIT } from '../../constants'
import { paramsFormatType, preProcessRegionParam } from '../datatypeRouters/_helpers'
import { TRPCError } from '@trpc/server'

export class RouterEdges extends RouterFilterBy {
  edgeCollection: string
  sourceSchemaName: string
  targetSchemaName: string
  secondaryEdgeCollection: string | undefined
  secondaryRouter: RouterEdges | undefined
  sourceSchemaCollection: string
  targetSchemaCollection: string
  sourceReturnStatements: string
  targetReturnStatements: string
  sourceSchema: Record<string, string>
  targetSchema: Record<string, string>

  constructor (schemaObj: configType, secondaryRouter: RouterEdges | undefined = undefined) {
    super(schemaObj)

    this.secondaryRouter = secondaryRouter

    this.edgeCollection = schemaObj.db_collection_name as string
    this.secondaryEdgeCollection = secondaryRouter?.edgeCollection as string

    const schema = loadSchemaConfig()

    const edge = schemaObj.relationship as Record<string, string>
    this.sourceSchemaName = edge.from
    this.targetSchemaName = edge.to
    this.sourceSchema = schema[this.sourceSchemaName] as Record<string, string>
    this.targetSchema = schema[this.targetSchemaName] as Record<string, string>

    this.sourceReturnStatements = new RouterFilterBy(this.sourceSchema).dbReturnStatements
    this.targetReturnStatements = new RouterFilterBy(this.targetSchema).dbReturnStatements

    this.sourceSchemaCollection = this.sourceSchema.db_collection_name
    this.targetSchemaCollection = this.targetSchema.db_collection_name
  }

  filterStatements (input: paramsFormatType, querySchema: Record<string, string>): string {
    const preProcessed = preProcessRegionParam(input)
    const router = new RouterFilterBy(querySchema)
    return router.getFilterStatements(preProcessed)
  }

  sortByStatement (sortBy: string): string {
    return sortBy !== '' ? `SORT record['${sortBy}']` : ''
  }

  // A --> B, given ID, return A and/or B that matches ID.
  async getBidirectionalByID (input: paramsFormatType, idName: string, page: number = 0, sortBy: string = '', verbose: boolean): Promise<any[]> {
    const recordId = input[idName] as string

    // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
    delete input[idName]

    const id = `${this.sourceSchemaCollection}/${decodeURIComponent(recordId)}`

    let filters = this.getFilterStatements(input)
    if (filters) {
      filters = ` AND ${filters}`
    }

    // assuming source and target have same schemas
    const verboseQuery = `
      FOR otherRecord in ${this.sourceSchemaCollection}
      FILTER otherRecord._key == otherRecordKey
      RETURN {${this.sourceReturnStatements.replaceAll('record', 'otherRecord')}}
    `

    const query = `
      FOR record IN ${this.edgeCollection}
        FILTER (record._from == '${id}' OR record._to == '${id}') ${filters}
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        LET otherRecordKey = PARSE_IDENTIFIER(record._from == '${id}' ? record._to : record._from).key
        RETURN {
          ${this.dbReturnStatements},
          '${this.sourceSchemaName}': ${verbose ? `(${verboseQuery})` : 'otherRecordKey'}
        }
    `

    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A -(edge)-> B, given ID for A and B, return A or B (opposite of ID match), and edge
  async getCompleteBidirectionalByID (input: paramsFormatType, idName: string, page: number = 0, sortBy: string = ''): Promise<any[]> {
    const recordId = input[idName] as string

    // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
    delete input[idName]

    const id = `${this.sourceSchemaCollection}/${decodeURIComponent(recordId)}`

    let filters = this.getFilterStatements(input)
    if (filters) {
      filters = ` AND ${filters}`
    }

    const query = `
        FOR record IN ${this.edgeCollection}
          FILTER (record._from == '${id}' OR record._to == '${id}') ${filters}
          ${this.sortByStatement(sortBy)}
          LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
          RETURN {[record._from == '${id}' ? '${this.sourceSchemaName}' : '${this.targetSchemaName}']: UNSET(DOCUMENT(record._from == '${id}' ? record._to : record._from), '_rev', '_id'), ${this.dbReturnStatements}}
    `

    /*
    Return follows the format, considering ID matches A in A --(edge)--> B:
    {
      B_collection_name: B_document,
      ...edge_properties
    }

    For example (genes/ENSG00000150456) --> (genes/ENSG00000121410), for ID: ENSG00000150456:
    {
      // Correspondent node
      "gene": DOCUMENT(genes/ENSG00000121410),

      // Edge properties
      "logit_score": -0.67,
      "source": "CoXPresdb",
      "source_url": "https://coxpresdb.jp/"
    }
    */

    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A -> B => given ID for A, return B
  async getTargetsByID (sourceId: string, page: number = 0, sortBy: string = '', verbose: boolean = false): Promise<any[]> {
    const verboseQuery = `
      FOR otherRecord IN ${this.targetSchemaCollection}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
      RETURN {${this.targetReturnStatements.replaceAll('record', 'otherRecord')}}
    `

    const query = `
      FOR record IN ${this.edgeCollection}
      FILTER record._from == '${this.sourceSchemaCollection}/${decodeURIComponent(sourceId)}'
      ${this.sortByStatement(sortBy)}
      LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN {
        '${this.targetSchemaName}': ${verbose ? `(${verboseQuery})` : 'record._to'},
        ${this.dbReturnStatements}
      }
    `

    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A -> B => given a query for A, return B
  async getTargets (input: paramsFormatType, sortBy: string = '', verbose: boolean = false, customFilter: string = ''): Promise<any[]> {
    const page = input.page as number

    if (customFilter !== '') {
      customFilter = `and ${customFilter}`
    }

    const verboseQuery = `
      FOR otherRecord IN ${this.targetSchemaCollection}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
      RETURN {${this.targetReturnStatements.replaceAll('record', 'otherRecord')}}
    `

    const query = `
      LET sources = (
        FOR record in ${this.sourceSchemaCollection}
        FILTER ${this.filterStatements(input, this.sourceSchema)}
        RETURN record._id
      )

      FOR record IN ${this.edgeCollection}
        FILTER record._from IN sources
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN {
          ${this.dbReturnStatements},
          '${this.targetSchemaName}': ${verbose ? `(${verboseQuery})` : 'record._to'}
        }
    `

    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A -> B => given ID for B, return A
  async getSourcesByID (targetId: string, page: number = 0, sortBy: string = '', verbose: boolean = false): Promise<any[]> {
    const verboseQuery = `
      FOR otherRecord IN ${this.sourceSchemaCollection}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
      RETURN {${this.sourceReturnStatements.replaceAll('record', 'otherRecord')}}
    `

    const query = `
      FOR record IN ${this.edgeCollection}
      FILTER record._to == '${this.targetSchemaCollection}/${decodeURIComponent(targetId)}'
      ${this.sortByStatement(sortBy)}
      LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN {
        '${this.sourceSchemaName}': ${verbose ? `(${verboseQuery})` : 'record._from'},
        ${this.dbReturnStatements}
      }
    `

    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A -> B => given a query for B, return A
  async getSources (input: paramsFormatType, sortBy: string = '', verbose: boolean = false, customFilter: string = ''): Promise<any[]> {
    const page = input.page as number

    if (customFilter !== '') {
      customFilter = `and ${customFilter}`
    }

    const verboseQuery = `
      FOR otherRecord IN ${this.sourceSchemaCollection}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
      RETURN {${this.sourceReturnStatements.replaceAll('record', 'otherRecord')}}
    `

    const query = `
      LET targets = (
        FOR record IN ${this.targetSchemaCollection}
        FILTER ${this.filterStatements(input, this.targetSchema)}
        RETURN record._id
      )

      FOR record IN ${this.edgeCollection}
        FILTER record._to IN targets ${customFilter}
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN {
          ${this.dbReturnStatements},
          '${this.sourceSchemaName}': ${verbose ? `(${verboseQuery})` : 'record._from'}
        }
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
        FOR record IN ${this.secondaryEdgeCollection as string}
        FILTER record._from IN primaryTargets
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN DISTINCT DOCUMENT(record._to)
      )

      FOR record IN secondaryTargets
        FILTER record != NULL
        RETURN {${this.secondaryRouter?.targetReturnStatements as string}}
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A -> B, B -> C => given a query for A, return C
  async getSecondaryTargets (input: paramsFormatType, sortBy: string = ''): Promise<any[]> {
    const page = input.page as number

    const query = `
      LET primarySources = (
        FOR record IN ${this.sourceSchemaCollection}
        FILTER ${this.filterStatements(input, this.sourceSchema)}
        RETURN record._id
      )

      LET primaryTargets = (
        FOR record IN ${this.edgeCollection}
        FILTER record._from IN primarySources
        RETURN record._to
      )

      LET secondaryTargets = (
        FOR record IN ${this.secondaryEdgeCollection as string}
        FILTER record._from IN primaryTargets
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN DISTINCT DOCUMENT(record._to)
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
        FOR record IN ${this.edgeCollection}
        FILTER record._to IN secondarySources
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN DISTINCT DOCUMENT(record._from)
      )

      FOR record in primarySources
        RETURN {${this.sourceReturnStatements}}
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A --(edge)--> B, (edge) --> C => given ID for C, return B
  async getPrimaryTargetFromHyperEdgeByID (targetId: string, page: number = 0, sortBy: string = '', customSecondaryFilter: string = '', verbose: boolean = false): Promise<any[]> {
    // C
    const secondaryTargetCollection = this.secondaryRouter?.targetSchemaCollection as string

    if (customSecondaryFilter !== '') {
      customSecondaryFilter = `and ${customSecondaryFilter}`
    }

    const verboseQuery = `
      FOR otherRecord IN ${this.targetSchemaCollection}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
      RETURN {${this.targetReturnStatements.replaceAll('record', 'otherRecord')}}
    `

    const query = `
      LET secondarySources = (
        FOR record IN ${this.secondaryEdgeCollection as string}
        FILTER record._to == '${secondaryTargetCollection}/${decodeURIComponent(targetId)}'
        RETURN PARSE_IDENTIFIER(record._from).key
      )

      FOR record IN ${this.edgeCollection}
      FILTER record._key IN secondarySources ${customSecondaryFilter}
      ${this.sortByStatement(sortBy)}
      LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN {
        '${this.targetSchemaName}': ${verbose ? `(${verboseQuery})` : 'record._to'},
        ${this.dbReturnStatements}
      }
    `

    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A --(edge)--> B, (edge) --> C => given a query for for C, return B
  async getPrimaryTargetsFromHyperEdge (input: paramsFormatType, page: number = 0, sortBy: string = '', customEdgeFilter = '', verbose: boolean = false): Promise<any[]> {
    // C
    const secondaryTargetCollection = this.secondaryRouter?.targetSchemaCollection as string
    const secondaryTargetFilters = this.filterStatements(input, this.secondaryRouter?.targetSchema as Record<string, string>)

    const verboseQuery = `
      FOR otherRecord IN ${this.targetSchemaCollection}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
      RETURN {${this.targetReturnStatements.replaceAll('record', 'otherRecord')}}
    `

    let query
    if (secondaryTargetFilters === '') {
      if (customEdgeFilter === '') {
        throw new TRPCError({
          code: 'BAD_REQUEST',
          message: 'At least one property must be defined.'
        })
      }

      query = `
        FOR record IN ${this.edgeCollection}
          FILTER ${customEdgeFilter}
          ${this.sortByStatement(sortBy)}
          LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
          RETURN {
            '${this.targetSchemaName}': ${verbose ? `(${verboseQuery})` : 'record._to'},
            ${this.dbReturnStatements}
          }
      `
    } else {
      if (customEdgeFilter !== '') {
        customEdgeFilter = `and ${customEdgeFilter}`
      }

      query = `
        LET secondaryTargets = (
          FOR record IN ${secondaryTargetCollection}
          FILTER ${secondaryTargetFilters}
          RETURN record._id
        )

        LET secondarySources = (
          FOR record IN ${this.secondaryEdgeCollection as string}
          FILTER record._to IN secondaryTargets
          RETURN record._from
        )

        FOR record IN ${this.edgeCollection}
          FILTER record._id IN secondarySources ${customEdgeFilter}
          ${this.sortByStatement(sortBy)}
          LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
          RETURN {
            '${this.targetSchemaName}': ${verbose ? `(${verboseQuery})` : 'record._to'},
            ${this.dbReturnStatements}
          }
      `
    }

    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A --(edge)--> B, (edge) --> C => given ID for B, return C's
  async getSecondaryTargetFromHyperEdgeByID (targetId: string, page: number = 0, sortBy: string = '', customPrimaryFilter = '', verbose: boolean = false): Promise<any[]> {
    // B
    const targetCollection = this.targetSchemaCollection

    // C
    const secondaryTargetCollection = this.secondaryRouter?.targetSchemaCollection as string
    const secondaryTargetReturn = this.secondaryRouter?.targetReturnStatements as string
    const secondaryTargetName = this.secondaryRouter?.targetSchemaName as string

    const verboseQuery = `
      FOR targetRecord IN ${secondaryTargetCollection}
        FILTER targetRecord._key == PARSE_IDENTIFIER(edgeRecord._to).key
        RETURN {${secondaryTargetReturn.replaceAll('record', 'targetRecord')}}
    `

    if (customPrimaryFilter !== '') {
      customPrimaryFilter = `and ${customPrimaryFilter}`
    }

    const query = `
      FOR record IN ${this.edgeCollection}
        FILTER record._to == '${targetCollection}/${targetId}' ${customPrimaryFilter}
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN (
          FOR edgeRecord IN ${this.secondaryEdgeCollection as string}
            FILTER edgeRecord._from == record._id
            RETURN {
              '${secondaryTargetName}': ${verbose ? `(${verboseQuery})` : 'edgeRecord._to'},
              ${this.dbReturnStatements}
            }
        )[0]
    `

    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A --(edge)--> B, (edge) --> C => given query for B, return C's
  async getSecondaryTargetsFromHyperEdge (input: paramsFormatType, page: number = 0, sortBy: string = '', queryOptions = '', customEdgeFilter = '', verbose: boolean = false): Promise<any[]> {
    // B
    const targetCollection = this.targetSchemaCollection

    // C
    const secondaryTargetCollection = this.secondaryRouter?.targetSchemaCollection as string
    const secondaryTargetReturn = this.secondaryRouter?.targetReturnStatements as string
    const secondaryTargetName = this.secondaryRouter?.targetSchemaName as string

    const primaryTargetFilters = this.filterStatements(input, this.targetSchema)

    const verboseQuery = `
      FOR targetRecord IN ${secondaryTargetCollection}
        FILTER targetRecord._key == PARSE_IDENTIFIER(edgeRecord._to).key
        RETURN {${secondaryTargetReturn.replaceAll('record', 'targetRecord')}}
    `

    let query
    if (primaryTargetFilters === '') {
      if (customEdgeFilter === '') {
        throw new TRPCError({
          code: 'BAD_REQUEST',
          message: 'At least one property must be defined.'
        })
      }

      query = `
        FOR record IN ${this.dbCollectionName}
          FILTER ${customEdgeFilter}
          ${this.sortByStatement(sortBy)}
          LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
          RETURN (
            FOR edgeRecord IN ${this.secondaryEdgeCollection as string}
              FILTER edgeRecord._from == record._id
              RETURN {
                '${secondaryTargetName}': ${verbose ? `(${verboseQuery})` : 'edgeRecord._to'},
                ${this.dbReturnStatements}
              }
          )[0]
      `
    } else {
      if (customEdgeFilter !== '') {
        customEdgeFilter = `and ${customEdgeFilter}`
      }

      query = `
        LET primaryTargets = (
          FOR record IN ${targetCollection} ${queryOptions}
          FILTER ${this.filterStatements(input, this.targetSchema)}
          RETURN record._id
        )

        FOR record in ${this.dbCollectionName}
          FILTER record._to IN primaryTargets ${customEdgeFilter}
          ${this.sortByStatement(sortBy)}
          LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
          RETURN (
            FOR edgeRecord IN ${this.secondaryEdgeCollection as string}
            FILTER edgeRecord._from == record._id
            RETURN {
              '${secondaryTargetName}': ${verbose ? `(${verboseQuery})` : 'edgeRecord._to'},
              ${this.dbReturnStatements}
            }
          )[0]
      `
    }

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
        FOR record IN ${this.secondaryEdgeCollection as string}
        FILTER record._to IN secondaryTargets
        RETURN record._from
      )

      LET primarySources = (
        FOR record IN ${this.edgeCollection}
        FILTER record._to IN secondarySources
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN DISTINCT DOCUMENT(record._from)
      )

      FOR record in primarySources
        RETURN {${this.sourceReturnStatements}}
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A --(edge)--> B, given a query for (edge) ->, return all (edge)s
  async getEdgeObjects (
    queryParams: Record<string, string | number | undefined>,
    queryOptions: string = '',
    verbose: boolean = false
  ): Promise<any[]> {
    let page = 0
    if (Object.hasOwn(queryParams, 'page')) {
      page = parseInt(queryParams.page as string)
    }

    let sortBy = ''
    if (Object.hasOwn(queryParams, 'sort')) {
      sortBy = `SORT record['${queryParams.sort as string}']`
    }

    const sourceReturn = `'${this.sourceSchemaName}': ${verbose ? 'DOCUMENT(record._from)' : 'record._from'},`
    const targetReturn = `'${this.targetSchemaName}': ${verbose ? 'DOCUMENT(record._to)' : 'record._to'},`

    const query = `
      FOR record IN ${this.edgeCollection} ${queryOptions}
      FILTER ${this.getFilterStatements(queryParams)}
      ${sortBy}
      LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN { ${sourceReturn + targetReturn + this.dbReturnStatements} }
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A --> B, given IDs list for A = {a1, a2, ...}, return {a1: [b's], a2: [b's], ...}
  async getTargetSet (
    listIds: string[],
    verbose: boolean = false
  ): Promise<any[]> {
    let targetFetch = 'targetsBySource[*].record._to'
    if (verbose) {
      targetFetch = 'DOCUMENT(targetsBySource[*].record._to)'
    }

    const query = `
      FOR record IN ${this.edgeCollection}
      FILTER record._from IN ['${listIds.join('\',\'')}']
      COLLECT source = record._from INTO targetsBySource
      RETURN {
          ${this.sourceSchemaCollection}: source,
          ${this.targetSchemaCollection}: ${targetFetch}
      }
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A --(edge)--> B, given autocomplete query for edge, return (edge) and B
  async getTargetEdgesByAutocompleteSearch (
    input: paramsFormatType,
    searchField: string,
    verbose: boolean = false): Promise<any[]> {
    const page = input.page as number
    const searchTerm = input[searchField] as string
    const searchViewName = `${this.dbCollectionName}_fuzzy_search_alias`

    // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
    delete input[searchField]

    const verboseQuery = `
      FOR otherRecord IN ${this.targetSchemaCollection}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
      RETURN {${this.targetReturnStatements.replaceAll('record', 'otherRecord')}}
    `

    let filters = this.getFilterStatements(input)
    if (filters !== '') {
      filters = `FILTER ${filters}`
    }

    const query = `
      FOR record IN ${searchViewName}
        SEARCH STARTS_WITH(record['${searchField}'], "${searchTerm}")
        SORT BM25(record) DESC
        ${filters}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN {
          ${this.dbReturnStatements},
          '${this.targetSchemaName}': ${verbose ? `(${verboseQuery})` : 'record._to'}
        }
    `

    const cursor = await db.query(query)
    return await cursor.all()
  }
}
