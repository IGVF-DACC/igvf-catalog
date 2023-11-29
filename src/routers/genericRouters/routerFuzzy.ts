import { Router } from './routerFactory'
import { RouterFilterBy } from './routerFilterBy'
import { db } from '../../database'
import { configType, QUERY_LIMIT } from '../../constants'
import { publicProcedure } from '../../trpc'
import { z } from 'zod'

export class RouterFuzzy extends RouterFilterBy implements Router {
  path: string
  hasGetByIDEndpoint = false

  constructor (schemaObj: configType) {
    super(schemaObj)

    this.path = `${this.apiName}/search/{term}`
  }

  searchViewName (): string {
    return `${this.dbCollectionName}_fuzzy_search_alias`
  }

  // Useful for incomplete search terms. E.g. query: "bran" => matches: "brain"
  levenshtein (searchField: string, searchTerm: string): string {
    return `LEVENSHTEIN_MATCH(
          record.${searchField},
          TOKENS("${decodeURIComponent(searchTerm)}", "text_en_no_stem")[0],
          1,    // max distance
          false // without transpositions
        )`
  }

  // Useful for complete search in long text fields. E.g. query: "brain" => matches: "brain" in long text fields such as descriptions and names
  multipleToken (searchField: string, searchTerm: string): string {
    return `TOKENS("${decodeURIComponent(searchTerm)}", "text_en_no_stem") ALL in record.${searchField}`
  }

  // Useful for prefix search. E.g. query: "brai" => matches: "brain"
  autocomplete (searchField: string, searchTerm: string): string {
    return `STARTS_WITH(record['${searchField}'], "${searchTerm}")`
  }

  async textSearch (searchQuery: Record<string, string>, method: string = '', page: number, customFilter: string = ''): Promise<any[]> {
    if (customFilter) {
      customFilter = `FILTER ${customFilter}`
    }

    const queryStatements: string[] = []
    Object.keys(searchQuery).forEach((searchField) => {
      if (searchQuery[searchField] !== undefined) {
        let statement = ''
        switch (method) {
          case 'autocomplete': {
            statement = this.autocomplete(searchField, searchQuery[searchField])
            break
          }
          case 'fuzzy': {
            statement = this.levenshtein(searchField, searchQuery[searchField])
            break
          }
          default: {
            statement = this.multipleToken(searchField, searchQuery[searchField])
          }
        }
        queryStatements.push(statement)
      }
    })

    const query = `
      FOR record IN ${this.searchViewName()}
        SEARCH ${queryStatements.join(' AND ')}
        ${customFilter}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        SORT BM25(record) DESC
        RETURN { ${this.dbReturnStatements} }
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }

  /*
  * Params:
  * term: query value to be autocompleted
  * page: results page number
  * apiReturn: true - return format complies with the /autocomplete endpoint, false - return format complies with the collection being queried
  * customFilter: a custom AQL filter that can be inserted in the autocomplete query
  * overWriteSearchField: autocomplete field is defined by the schemaConfig, this option allows a custom field to be used in the query
  */
  async autocompleteSearch (term: string, page: number, apiReturn: boolean = false, customFilter: string = '', overWriteSearchField: string = ''): Promise<any[]> {
    // supporting only one search field for now
    let searchField = this.fuzzyTextSearch[0]

    // in case of arrays, [*] is not required in the query
    searchField = searchField.replace('[*]', '')

    if (overWriteSearchField) {
      searchField = overWriteSearchField
    }

    let dbReturn = this.dbReturnStatements
    if (apiReturn) {
      dbReturn = `term: record['${searchField}'], uri: CONCAT('/${this.apiName}/', record['_key'])`
    }

    if (customFilter) {
      customFilter = `FILTER ${customFilter}`
    }

    term = term.toLowerCase()

    const query = `
      FOR record IN ${this.searchViewName()}
        SEARCH STARTS_WITH(record['${searchField}'], "${term}")
        SORT BM25(record) DESC
        ${customFilter}
        LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
        RETURN { ${dbReturn} }
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }

  generateRouter (): any {
    const inputFormat = z.object({ term: z.string().trim(), page: z.number().optional() })
    const outputFormat = z.array(z.object(this.resolveTypes(this.output, true, false)))

    return publicProcedure
      .meta({ openapi: { method: 'GET', path: `/${this.path}` } })
      .input(inputFormat)
      .output(outputFormat)
      .query(async ({ input }) => await this.autocompleteSearch(input.term, input.page ?? 0))
  }
}
