import { Router } from './routerFactory'
import { z } from 'zod'
import { db } from '../../database'
import { publicProcedure } from '../../trpc'
import { configType, QUERY_LIMIT, PROPERTIES_TO_ZOD_MAPPING } from '../../constants'

export class RouterFilterBy implements Router {
  apiName: string
  apiSpecs: Record<string, string>
  properties: Record<string, string>
  filterBy: string[]
  filterByRange: string[]
  fuzzyTextSearch: string[]
  output: string[]
  simplifiedOutput: string[] | null
  hasGetByIDEndpoint: boolean
  dbCollectionName: string
  dbCollectionPerChromosome: boolean
  dbReturnStatements: string
  simplifiedDbReturnStatements: string

  constructor (schemaObj: configType) {
    this.apiSpecs = schemaObj.accessible_via as Record<string, string>
    this.apiName = this.apiSpecs.name
    this.properties = schemaObj.properties as Record<string, string>
    this.filterBy = this.apiSpecs.filter_by?.split(',').map((item: string) => item.trim()) || []
    this.filterByRange = this.apiSpecs.filter_by_range?.split(',').map((item: string) => item.trim()) || []
    this.output = this.apiSpecs.return.split(',').map((item: string) => item.trim())
    this.simplifiedOutput = this.apiSpecs.simplified_return?.split(',').map((item: string) => item.trim())
    this.hasGetByIDEndpoint = this.filterBy.includes('_id')
    this.fuzzyTextSearch = this.apiSpecs.fuzzy_text_search?.split(',').map((item: string) => item.trim()) || []
    this.dbCollectionName = schemaObj.db_collection_name as string
    this.dbCollectionPerChromosome = !!schemaObj.db_collection_per_chromosome

    let returns: string[] = []
    this.output.forEach((field: string) => {
      if (field === '_id') {
        returns.push('_id: record._key')
      } else if (this.properties[field] === 'int') {
        returns.push(`'${field}': record['${field}:long']`)
      } else {
        returns.push(`'${field}': record['${field}']`)
      }
    })
    this.dbReturnStatements = returns.join(', ')
    this.simplifiedDbReturnStatements = this.dbReturnStatements

    if (this.simplifiedOutput) {
      returns = []
      this.simplifiedOutput.forEach((field: string) => {
        if (this.properties[field] === 'int') {
          returns.push(`'${field}': record['${field}:long']`)
        } else {
          returns.push(`'${field}': record['${field}']`)
        }
      })
      this.simplifiedDbReturnStatements = returns.join(', ')
    }
  }

  getFilterStatements (
    queryParams: Record<string, string | number | undefined>,
    joinBy: string = 'and'
  ): string {
    const dbFilterBy: string[] = []

    Object.keys(queryParams).forEach((element: string) => {
      // reserved parameters for pagination and verbose mode
      if (element === 'page' || element === 'sort' || element === 'verbose') {
        return
      }

      if (queryParams[element] !== undefined) {
        // 'interesect' is a reserved parameter for intersectional region search
        // 'annotation.freq' is a special case for variant data
        if (this.filterByRange.includes(element) || element === 'intersect' || element.startsWith('annotations.freq')) {
          const value = queryParams[element]?.toString()

          let stringOperator = null
          let operand = value as unknown as number

          if (value?.includes(':')) {
            const pair = value.split(':')
            stringOperator = pair[0]
            operand = pair[1] as unknown as number
          }

          // e.g: input['intersect'] = 'start-end:12345-54321'
          if (element === 'intersect') {
            const rangeValue = value?.split(':') as string[]
            const fieldOperands = rangeValue[0].split('-')
            const rangeOperands = rangeValue[1].split('-')

            // e.g.:fieldOperands[0] = start, fieldOperands[1] = end
            // e.g.:rangeOperands[0] = 12345, rangeOperands[1] = 54321
            const intersectionConditionals = [
              `(record['${fieldOperands[1]}:long'] >= ${rangeOperands[0]} AND record['${fieldOperands[1]}:long'] <= ${rangeOperands[1]})`,
              `(record['${fieldOperands[0]}:long'] >= ${rangeOperands[0]} AND record['${fieldOperands[0]}:long'] <= ${rangeOperands[1]})`,
              `(record['${fieldOperands[1]}:long'] >= ${rangeOperands[0]} AND record['${fieldOperands[0]}:long'] <= ${rangeOperands[1]})`
            ]
            dbFilterBy.push(`(${intersectionConditionals.join(' OR ')})`)
            return
          }

          if (stringOperator === 'range') {
            const rangeValue = value?.split(':') as string[]
            const rangeOperands = rangeValue[1].split('-')

            if (!element.endsWith(':long')) {
              const elements = element.split('.')

              // e.g: record.position => record['position:long']
              if (elements.length === 1) {
                element = `record['${element}:long']`
              } else {
                // e.g: record.annotation.freq.100genome.alt => record.annotation.freq[100genome]['alt:long']
                const lastElement = elements.pop() as string
                const secondLastElement = elements.pop() as string // case of variant sources, e.g. 100genome
                element = `record.${elements.join('.')}['${secondLastElement}']['${lastElement}:long']`
              }
            }

            dbFilterBy.push(`${element} >= ${rangeOperands[0]} and ${element} <= ${rangeOperands[1]}`)
            return
          }

          let operator
          switch (stringOperator) {
            case 'gt':
              operator = '>'
              break
            case 'gte':
              operator = '>='
              break
            case 'lt':
              operator = '<'
              break
            case 'lte':
              operator = '<='
              break
            default:
              operator = '=='
          }

          dbFilterBy.push(`record['${element}:long'] ${operator} ${operand}`)
        } else {
          if (element === 'dbxrefs') {
            dbFilterBy.push(`'${queryParams[element] as string | number}' in record.${element}[*].id`)
          } else if (this.properties[element] === 'array') {
            dbFilterBy.push(`'${queryParams[element] as string | number}' in record.${element}`)
          } else {
            dbFilterBy.push(`record.${element} == '${queryParams[element] as string | number}'`)
          }
        }
      }
    })

    return dbFilterBy.join(` ${joinBy} `) // default: 'and'
  }

  async getObjectIDs (
    queryParams: Record<string, string | number | undefined>,
    queryOptions: string = '',
    exclusiveJoin: boolean = true
  ): Promise<any[]> {
    let page = 0
    if (Object.hasOwn(queryParams, 'page')) {
      page = parseInt(queryParams.page as string)
    }

    let sortBy = ''
    if (Object.hasOwn(queryParams, 'sort')) {
      sortBy = `SORT record['${queryParams.sort as string}']`
    }

    const query = `
      FOR record IN ${this.dbCollectionName} ${queryOptions}
      FILTER ${this.getFilterStatements(queryParams, exclusiveJoin ? 'and' : 'or')}
      ${sortBy}
      LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN DISTINCT record._id
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }

  async getObjects (
    queryParams: Record<string, string | number | undefined>,
    queryOptions: string = ''
  ): Promise<any[]> {
    let collectionName = this.dbCollectionName
    if (this.dbCollectionPerChromosome) {
      collectionName = `${this.dbCollectionName}_${queryParams.chr as string}`
    }

    let page = 0
    if (Object.hasOwn(queryParams, 'page')) {
      page = parseInt(queryParams.page as string)
    }

    let sortBy = ''
    if (Object.hasOwn(queryParams, 'sort')) {
      sortBy = `SORT record['${queryParams.sort as string}']`
    }

    let filterBy = ''
    const filterSts = this.getFilterStatements(queryParams)
    if (filterSts !== '') {
      filterBy = `FILTER ${filterSts}`
    }

    const query = `
      FOR record IN ${collectionName} ${queryOptions}
      ${filterBy}
      ${sortBy}
      LIMIT ${page * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN { ${this.dbReturnStatements} }
    `
    const cursor = await db.query(query)
    return await cursor.all()
  }

  resolveTypes (params: string[], addID: boolean, allStrings: boolean): Record<string, z.ZodType> {
    const paramTypes: Record<string, z.ZodType> = {}

    params.filter(p => addID || p !== '_id').forEach((param: string) => {
      if (allStrings) {
        paramTypes[param] = z.string().optional()
      } else {
        paramTypes[param] = PROPERTIES_TO_ZOD_MAPPING[this.properties[param]] ?? z.string().optional()
      }
    })

    return paramTypes
  }

  generateRouter (): any {
    const path = `/${this.apiName}` as const
    const inputFormat = z.object({ ...this.resolveTypes(this.filterBy, false, false), ...this.resolveTypes(this.filterByRange, false, true) })
    const outputFormat = z.array(z.object(this.resolveTypes(this.output, true, false)))

    return publicProcedure
      .meta({ openapi: { method: 'GET', path, description: this.apiSpecs.description } })
      .input(inputFormat)
      .output(outputFormat)
      .query(async ({ input }) => await this.getObjects(input))
  }
}
