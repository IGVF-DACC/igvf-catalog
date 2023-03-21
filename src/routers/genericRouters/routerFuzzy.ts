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

  async getObjectsByFuzzyTextSearch (term: string, page: number): Promise<any[]> {
    // supporting only one search field for now
    const searchField = this.fuzzyTextSearch[0]

    const query = `
      FOR record IN ${this.searchViewName()}
        SEARCH LEVENSHTEIN_MATCH(
          record.${searchField},
          TOKENS("${decodeURIComponent(term)}", "text_en_no_stem")[0],
          1,    // max distance
          false // without transpositions
        )
        SORT BM25(record) DESC
        LIMIT ${page}, ${QUERY_LIMIT}
        RETURN { ${this.dbReturnStatements} }
    `

    const cursor = await db.query(query)
    const records = await cursor.all()

    console.log(records)
    return records
  }

  generateRouter (): any {
    const inputFormat = z.object({ term: z.string(), page: z.number().optional() })
    const outputFormat = z.array(this.resolveTypes(this.output, true))

    return publicProcedure
      .meta({ openapi: { method: 'GET', path: `/${this.path}` } })
      .input(inputFormat)
      .output(outputFormat)
      .query(async ({ input }) => await this.getObjectsByFuzzyTextSearch(input.term, input.page ?? 0))
  }
}
