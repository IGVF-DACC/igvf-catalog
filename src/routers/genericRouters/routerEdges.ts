import { RouterFilterBy } from './routerFilterBy'
import { loadSchemaConfig } from './genericRouters'
import { db } from '../../database'
import { configType, QUERY_LIMIT } from '../../constants'
import { paramsFormatType, preProcessRegionParam, verboseItems } from '../datatypeRouters/_helpers'
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

  // A --(edge)--> B, given query in nodes collection for A or B (and edge filters), return A and B that matches the query.
  // For example:
  // Given input parameters: protein_name == 'CTCF_HUMAN'
  // Returns all pairs of proteins in proteins_proteins collection, where either _from or _to matches with the protein_name in input in proteins collection
  // Returns format: 'protein 1': ...; 'protein 2': ...; Edge properties...;
  async getBidirectionalByNode (input: paramsFormatType, sortBy: string = '', customFilter: string = '', verbose: boolean): Promise<any[]> {
    const page = input.page as number

    const sourceVerboseQuery = `
    FOR otherRecord IN ${this.sourceSchemaCollection}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${this.sourceReturnStatements.replaceAll('record', 'otherRecord')}}
  `
    const targetVerboseQuery = `
    FOR otherRecord IN ${this.targetSchemaCollection}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${this.targetReturnStatements.replaceAll('record', 'otherRecord')}}
  `

    let query
    // assuming source and target have same schemas
    const NodeFilter = this.filterStatements(input, this.sourceSchema)
    // if only search by edge filters
    if (NodeFilter === '') {
      query = `
        FOR record IN ${this.edgeCollection}
          FILTER ${customFilter}
          ${this.sortByStatement(sortBy)}
          LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
          RETURN {
            '${this.sourceSchemaName.concat(' 1')}': ${verbose ? `(${sourceVerboseQuery})` : 'record._from'},
            '${this.sourceSchemaName.concat(' 2')}': ${verbose ? `(${targetVerboseQuery})` : 'record._to'},
            ${this.dbReturnStatements}
          }
        `
    } else {
      if (customFilter !== '') {
        customFilter = `and ${customFilter}`
      }

      query = `
      LET nodes = (
        FOR record in ${this.sourceSchemaCollection}
        FILTER ${NodeFilter}
        RETURN record._id
      )

      FOR record IN ${this.edgeCollection}
        FILTER (record._from IN nodes OR record._to IN nodes) ${customFilter}
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN {
          '${this.sourceSchemaName.concat(' 1')}': ${verbose ? `(${sourceVerboseQuery})` : 'record._from'},
          '${this.sourceSchemaName.concat(' 2')}': ${verbose ? `(${targetVerboseQuery})` : 'record._to'},
          ${this.dbReturnStatements}
        }
      `
    }

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

    const verboseQuery = `
      FOR otherRecord IN ${this.targetSchemaCollection}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
      RETURN {${this.targetReturnStatements.replaceAll('record', 'otherRecord')}}
    `

    const query = `
      LET sources = (
        FOR record in ${this.sourceSchemaCollection}
        FILTER ${this.filterStatements(input, this.sourceSchema)} ${customFilter}
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

  // A -> B => given a query for A, and filter on edge collection, return B
  async getTargetsWithEdgeFilter (input: paramsFormatType, sortBy: string = '', queryOptions = '', verbose: boolean = false, edgeFilter: string = ''): Promise<any[]> {
    const page = input.page as number

    if (edgeFilter !== '') {
      edgeFilter = `and ${edgeFilter}`
    }

    const verboseQuery = `
      FOR otherRecord IN ${this.targetSchemaCollection}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
      RETURN {${this.targetReturnStatements.replaceAll('record', 'otherRecord')}}
    `

    const query = `
      LET sources = (
        FOR record in ${this.sourceSchemaCollection} ${queryOptions}
        FILTER ${this.filterStatements(input, this.sourceSchema)}
        RETURN record._id
      )

      FOR record IN ${this.edgeCollection}
        FILTER record._from IN sources ${edgeFilter}
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

  // A -> B => given a query for A, return B and verbose edge property
  /*
  For example:
  // Edge property in regulatory_regions_genes:
  biological_conext: ontology_terms/EFO_0009495
  // Input parameters
  verboseProp = 'biological_conext', verbosePropField = 'term_name'

  -> returns term_name of EFO_0009495 in ontology_terms collection, along with other edge properties
  */
  async getTargetsWithVerboseProp (input: paramsFormatType, sortBy: string = '', verbose: boolean = false, customFilter: string = '', verboseProp: string = '', verbosePropField: string = ''): Promise<any[]> {
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
        FILTER record._from IN sources ${customFilter}
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN {
          ${this.dbReturnStatements},
          '${verbosePropField}': DOCUMENT(record['${verboseProp}'])['${verbosePropField}'],
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

  // A -> B => given a query for B, return A and verbose edge property
  // See example in getTargetsWithVerboseProp
  async getSourcesWithVerboseProp (input: paramsFormatType, sortBy: string = '', verbose: boolean = false, customFilter: string = '', verboseProp: string = '', verbosePropField: string = ''): Promise<any[]> {
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
          '${verbosePropField}': DOCUMENT(record['${verboseProp}'])['${verbosePropField}'],
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

  // A --(edge)--> B, (edge) --(hyperedge)--> C => given ID for C, return A and B, and properties from hyperedge
  async getPrimaryPairFromHyperEdgeByID (targetId: string, page: number = 0, sortBy: string = '', customSecondaryFilter: string = '', verbose: boolean = false): Promise<any[]> {
    // A
    const sourceVerboseQuery = `
      FOR otherRecord IN ${this.sourceSchemaCollection}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
      RETURN {${this.sourceReturnStatements.replaceAll('record', 'otherRecord')}}
    `
    // C
    const secondaryTargetCollection = this.secondaryRouter?.targetSchemaCollection as string

    if (customSecondaryFilter !== '') {
      customSecondaryFilter = `and ${customSecondaryFilter}`
    }

    // B
    const targetVerboseQuery = `
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
      RETURN (
        FOR edgeRecord IN ${this.secondaryEdgeCollection as string}
        FILTER edgeRecord._from == record._id
        RETURN {
          '${this.sourceSchemaName}': ${verbose ? `(${sourceVerboseQuery})` : 'record._from'},
          '${this.targetSchemaName}': ${verbose ? `(${targetVerboseQuery})` : 'record._to'},
          ${this.secondaryRouter?.dbReturnStatements.replaceAll('record', 'edgeRecord') as string}
        }
      )[0]
    `

    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A --(edge)--> B, (edge) --> C => given ID for B, return C's
  async getSecondaryTargetFromHyperEdgeByID (targetId: string, page: number = 0, sortBy: string = '', customPrimaryFilter = '', verbose: boolean = false, extraDataFrom: string = 'edge'): Promise<any[]> {
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
              ${extraDataFrom === 'edge' ? `${this.dbReturnStatements}` : `${this.secondaryRouter?.dbReturnStatements.replaceAll('record', 'edgeRecord') as string}`}
            }
        )[0]
    `

    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A --(edge)--> B, (edge) --> C => given query for B, return C's
  async getSecondaryTargetsFromHyperEdge (input: paramsFormatType, page: number = 0, sortBy: string = '', queryOptions = '', customEdgeFilter = '', verbose: boolean = false, extraDataFrom: string = 'edge'): Promise<any[]> {
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
                ${extraDataFrom === 'edge' ? `${this.dbReturnStatements}` : `${this.secondaryRouter?.dbReturnStatements.replaceAll('record', 'edgeRecord') as string}`}
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
              ${extraDataFrom === 'edge' ? `${this.dbReturnStatements}` : `${this.secondaryRouter?.dbReturnStatements.replaceAll('record', 'edgeRecord') as string}`}
            }
          )[0]
      `
    }

    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A --(edge)--> B, (edge) --(hyperedge)--> C => given query for B, return A,B,C's and (edge) and/or (hyperedge)
  async getSecondaryTargetsAndEdgeObjectsByTargets (input: paramsFormatType, page: number = 0, sortBy: string = '', queryOptions = '', customEdgeFilter = '', verbose: boolean = false, extraDataFrom: string = 'edge'): Promise<any[]> {
    // A
    const sourceName = this.sourceSchemaName
    const sourceVerboseQuery = `
      FOR otherRecord IN ${this.sourceSchemaCollection}
        FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
        RETURN {${this.sourceReturnStatements.replaceAll('record', 'otherRecord')}}
    `

    // B
    const targetName = this.targetSchemaName
    const targetCollection = this.targetSchemaCollection
    const targetVerboseQuery = `
    FOR otherRecord IN ${this.targetSchemaCollection}
      FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
      RETURN {${this.targetReturnStatements.replaceAll('record', 'otherRecord')}}
  `

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
                '${sourceName}': ${verbose ? `(${sourceVerboseQuery})` : 'record._from'},
                '${targetName}': ${verbose ? `(${targetVerboseQuery})` : 'record._to'},
                '${secondaryTargetName}': ${verbose ? `(${verboseQuery})` : 'edgeRecord._to'},
                ${this.dbReturnStatements},
                ${extraDataFrom === 'edge' ? '' : `${this.secondaryRouter?.dbReturnStatements.replaceAll('record', 'edgeRecord') as string}`}
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
              '${sourceName}': ${verbose ? `(${sourceVerboseQuery})` : 'record._from'},
              '${targetName}': ${verbose ? `(${targetVerboseQuery})` : 'record._to'},
              '${secondaryTargetName}': ${verbose ? `(${verboseQuery})` : 'edgeRecord._to'},
              ${this.dbReturnStatements},
              ${extraDataFrom === 'edge' ? '' : `${this.secondaryRouter?.dbReturnStatements.replaceAll('record', 'edgeRecord') as string}`}
            }
          )[0]
      `
    }

    const cursor = await db.query(query)
    return await cursor.all()
  }

  // A --(edge)--> B, (edge) --(hyperedge)--> C => given query for A, return A,B,C's and (edge) and/or (hyperedge)
  async getSecondaryTargetsAndEdgeObjectsBySource (input: paramsFormatType, page: number = 0, sortBy: string = '', queryOptions = '', customEdgeFilter = '', verbose: boolean = false, extraDataFrom: string = 'edge'): Promise<any[]> {
    // A
    const sourceCollection = this.sourceSchemaCollection
    const sourceName = this.sourceSchemaName

    const sourceVerboseQuery = `
      FOR otherRecord IN ${this.sourceSchemaCollection}
        FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
        RETURN {${this.sourceReturnStatements.replaceAll('record', 'otherRecord')}}
    `

    // B
    const targetName = this.targetSchemaName
    const targetVerboseQuery = `
      FOR otherRecord IN ${this.targetSchemaCollection}
        FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
        RETURN {${this.targetReturnStatements.replaceAll('record', 'otherRecord')}}
    `

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
                '${sourceName}': ${verbose ? `(${sourceVerboseQuery})` : 'record._from'},
                '${targetName}': ${verbose ? `(${targetVerboseQuery})` : 'record._to'},
                '${secondaryTargetName}': ${verbose ? `(${verboseQuery})` : 'edgeRecord._to'},
                ${this.dbReturnStatements},
                ${extraDataFrom === 'edge' ? '' : `${this.secondaryRouter?.dbReturnStatements.replaceAll('record', 'edgeRecord') as string}`}
              }
          )[0]
      `
    } else {
      if (customEdgeFilter !== '') {
        customEdgeFilter = `and ${customEdgeFilter}`
      }

      query = `
      LET primaryTargets = (
        FOR record IN ${sourceCollection} ${queryOptions}
        FILTER ${this.filterStatements(input, this.sourceSchema)}
        RETURN record._id
      )

      FOR record in ${this.dbCollectionName}
        FILTER record._from IN primaryTargets ${customEdgeFilter}
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN (
          FOR edgeRecord IN ${this.secondaryEdgeCollection as string}
          FILTER edgeRecord._from == record._id
          RETURN {
            '${sourceName}': ${verbose ? `(${sourceVerboseQuery})` : 'record._from'},
            '${targetName}': ${verbose ? `(${targetVerboseQuery})` : 'record._to'},
            '${secondaryTargetName}': ${verbose ? `(${verboseQuery})` : 'edgeRecord._to'},
            ${this.dbReturnStatements},
            ${extraDataFrom === 'edge' ? '' : `${this.secondaryRouter?.dbReturnStatements.replaceAll('record', 'edgeRecord') as string}`}
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
    verbose: boolean = false,
    customFilters: string = ''
  ): Promise<any[]> {
    let page = 0
    if (Object.hasOwn(queryParams, 'page')) {
      page = parseInt(queryParams.page as string)
    }

    let sortBy = ''
    if (Object.hasOwn(queryParams, 'sort')) {
      sortBy = `SORT record['${queryParams.sort as string}']`
    }

    const sourceQuery = `FOR otherRecord IN ${this.sourceSchemaCollection}
      FILTER otherRecord._id == record._from
      RETURN {${this.sourceReturnStatements.replaceAll('record', 'otherRecord')}}
    `

    const targetQuery = `
      FOR otherRecord IN ${this.targetSchemaCollection}
      FILTER otherRecord._id == record._to
      RETURN {${this.targetReturnStatements.replaceAll('record', 'otherRecord')}}
    `

    const sourceReturn = `'${this.sourceSchemaName}': ${verbose ? `(${sourceQuery})[0]` : 'record._from'},`
    const targetReturn = `'${this.targetSchemaName}': ${verbose ? `(${targetQuery})[0]` : 'record._to'},`

    if (customFilters !== '') {
      customFilters = ` AND ${customFilters}`
    }

    const query = `
      FOR record IN ${this.edgeCollection} ${queryOptions}
      FILTER ${this.getFilterStatements(queryParams)} ${customFilters}
      ${sortBy}
      LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN { ${sourceReturn + targetReturn + this.dbReturnStatements} }
    `

    const cursor = await db.query(query)
    return await cursor.all()
  }

  // Given id for C, and C --(edge)--> A, and C --(edge)--> B
  // return all matching edges and corresponding A's and B's
  async getTargetSetByUnion (id: string, page: number, verbose: boolean = false): Promise<any[]> {
    // find all edges from C -> A, that matches IDs for A
    const A = `
    LET A = (
      FOR record in ${this.edgeCollection}
      FILTER record._from == '${id}'
      SORT record._to
      COLLECT from = record._from, to = record._to INTO sources = record._id
      RETURN {
        '${this.sourceSchemaName}': from,
        'related': { '${this.targetSchemaName}': to, 'sources': sources }
      })`

    // find all edges from C -> B, that matches IDs for B
    const secondaryTargetName = this.secondaryRouter?.targetSchemaName as string
    const secondarySourceName = this.secondaryRouter?.sourceSchemaName as string
    const secondaryTargetCollection = this.secondaryRouter?.targetSchemaCollection as string
    const secondaryTargetSchema = this.secondaryRouter?.targetSchema as Record<string, string>
    const B = `
    LET B = (
      FOR record in ${this.secondaryEdgeCollection as string}
      FILTER record._from == '${id}'
      SORT record._to
      COLLECT from = record._from, to = record._to INTO sources = record._id
      RETURN {
        '${secondarySourceName}': from,
        'related': { '${secondaryTargetName}': to, 'sources': sources }
      })`

    let C = 'source'
    if (verbose) {
      const sts = new RouterFilterBy(this.sourceSchema).simplifiedDbReturnStatements.replaceAll('record', 'otherRecord')
      C = `(
        FOR otherRecord in ${this.sourceSchemaCollection}
        FILTER otherRecord._id == source
        RETURN {${sts}}
      )[0]`
    }

    // group results from A and B by C
    const query = `
      ${A}
      ${B}

      FOR record in UNION(A, B)
      COLLECT source = record['${secondarySourceName}'] INTO relatedObjs = record.related
      LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN {
        '${secondarySourceName}': ${C},
        'related': relatedObjs
      }
    `

    const objs = await (await db.query(query)).all()

    if (!verbose) {
      return objs
    }

    // Verbose mode:
    // list all unique objects from collections A and B
    const AItems = new Set<string>()
    const BItems = new Set<string>()
    objs.forEach(obj => {
      obj.related.forEach((related: Record<string, any>) => {
        if (related[this.targetSchemaName] !== undefined) {
          AItems.add(related[this.targetSchemaName])
        }

        if (related[secondaryTargetName] !== undefined) {
          BItems.add(related[secondaryTargetName])
        }
      })
    })

    const primaryItems = await verboseItems(this.targetSchemaCollection, Array.from(AItems), this.targetSchema)
    const secondaryItems = await verboseItems(secondaryTargetCollection, Array.from(BItems), secondaryTargetSchema)
    const dictionary = Object.assign({}, primaryItems, secondaryItems)

    objs.forEach(obj => {
      obj.related.forEach((related: Record<string, any>) => {
        if (related[this.targetSchemaName] !== undefined && dictionary[related[this.targetSchemaName]] !== undefined) {
          related[this.targetSchemaName] = dictionary[related[this.targetSchemaName]]
        }

        if (related[secondaryTargetName] !== undefined && dictionary[related[this.targetSchemaName]] !== undefined) {
          related[this.targetSchemaName] = dictionary[related[this.targetSchemaName]]
        }
      })
    })

    return objs
  }

  // Given ids [x1, x2, ...] for collections A and/or B, and, C --(edge)--> A, and C --(edge)--> B
  // return all matching edges and C's
  async getSourceSetByUnion (listIds: string[], page: number, verbose: boolean = false): Promise<any[]> {
    // find all edges from C -> A, that matches IDs for A
    const A = `
    LET A = (
      FOR record in ${this.edgeCollection}
      FILTER record._to IN ['${listIds.join('\',\'')}']
      SORT record._from
      COLLECT from = record._from, to = record._to INTO sources = record._id
      RETURN {
        '${this.sourceSchemaName}': from,
        'related': { '${this.targetSchemaName}': to, 'sources': sources }
      })`

    // find all edges from C -> B, that matches IDs for B
    const secondaryTargetName = this.secondaryRouter?.targetSchemaName as string
    const secondarySourceName = this.secondaryRouter?.sourceSchemaName as string
    const secondaryTargetCollection = this.secondaryRouter?.targetSchemaCollection as string
    const secondaryTargetSchema = this.secondaryRouter?.targetSchema as Record<string, string>
    const B = `
    LET B = (
      FOR record in ${this.secondaryEdgeCollection as string}
      FILTER record._to IN ['${listIds.join('\',\'')}']
      SORT record._from
      COLLECT from = record._from, to = record._to INTO sources = record._id
      RETURN {
        '${secondarySourceName}': from,
        'related': { '${secondaryTargetName}': to, 'sources': sources }
      })`

    let C = 'source'
    if (verbose) {
      const sts = new RouterFilterBy(this.sourceSchema).simplifiedDbReturnStatements.replaceAll('record', 'otherRecord')
      C = `(
        FOR otherRecord in ${this.sourceSchemaCollection}
        FILTER otherRecord._id == source
        RETURN {${sts}}
      )[0]`
    }

    // group results from A and B by C
    const query = `
      ${A}
      ${B}

      FOR record in UNION(A, B)
      COLLECT source = record['${secondarySourceName}'] INTO relatedObjs = record.related
      LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN {
        '${secondarySourceName}': ${C},
        'related': relatedObjs
      }
    `

    const objs = await (await db.query(query)).all()

    if (!verbose) {
      return objs
    }

    // Verbose mode:
    // list all unique objects from collections A and B
    const AItems = new Set<string>()
    const BItems = new Set<string>()
    objs.forEach(obj => {
      obj.related.forEach((related: Record<string, any>) => {
        if (related[this.targetSchemaName] !== undefined) {
          AItems.add(related[this.targetSchemaName])
        }

        if (related[secondaryTargetName] !== undefined) {
          BItems.add(related[secondaryTargetName])
        }
      })
    })

    const primaryItems = await verboseItems(this.targetSchemaCollection, Array.from(AItems), this.targetSchema)
    const secondaryItems = await verboseItems(secondaryTargetCollection, Array.from(BItems), secondaryTargetSchema)
    const dictionary = Object.assign({}, primaryItems, secondaryItems)

    objs.forEach(obj => {
      obj.related.forEach((related: Record<string, any>) => {
        if (related[this.targetSchemaName] !== undefined && dictionary[related[this.targetSchemaName]] !== undefined) {
          related[this.targetSchemaName] = dictionary[related[this.targetSchemaName]]
        }

        if (related[secondaryTargetName] !== undefined && dictionary[related[this.targetSchemaName]] !== undefined) {
          related[this.targetSchemaName] = dictionary[related[this.targetSchemaName]]
        }
      })
    })

    return objs
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

  // A --(edge)--> B, given textual token query for edge, return (edge) and B
  async getTargetEdgesByTokenTextSearch (
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
        SEARCH TOKENS("${decodeURIComponent(searchTerm)}", "text_en_no_stem") ALL in record.${searchField}
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

  // A --> B --> C, given B, return all A's if opt == parent, or return all C's if opt == children
  // assuming A, B, C are all of the same type
  async getChildrenParents (id: string, opt: string, sortBy: string, page: number): Promise<any[]> {
    const query = `
      FOR record IN ${this.edgeCollection}
        LET details = (
          FOR otherRecord IN ${this.targetSchemaCollection}
          FILTER otherRecord._id == record.${opt === 'children' ? '_to' : '_from'}
          RETURN {${this.targetReturnStatements.replaceAll('record', 'otherRecord')}}
        )[0]

        FILTER record.${opt === 'children' ? '_from' : '_to'} == '${this.sourceSchemaCollection}/${decodeURIComponent(id)}' && details != null
        ${this.sortByStatement(sortBy)}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}

        RETURN {
          'term': details,
          'relationship_type': record.type || 'null'
        }
    `

    const cursor = await db.query(query)
    return await cursor.all()
  }
}
