import { TRPCError } from '@trpc/server'
import { RouterFilterBy } from '../genericRouters/routerFilterBy'
import { db } from '../../database'
import { configType } from '../../constants'

export type paramsFormatType = Record<string, string | number | undefined>

export function validRegion (region: string): string[] | null {
  const regex: RegExp = /(chr\w+):(\d*)-(\d*)/

  if (regex.test(region)) {
    const breakdown = regex.exec(region)
    if (breakdown === null || breakdown.length < 4) {
      return null
    }
    return breakdown
  }

  return null
}

export function preProcessRegionParam (input: paramsFormatType, singleFieldRangeQueryDB: string | null = null, regionParamPrefix: string = ''): paramsFormatType {
  const newInput = input

  let chrField = 'chr'
  let startField = 'start'
  let endField = 'end'
  let regionField = 'region'

  if (regionParamPrefix !== '') {
    chrField = `${regionParamPrefix}_${chrField}`
    startField = `${regionParamPrefix}_${startField}`
    endField = `${regionParamPrefix}_${endField}`
    regionField = `${regionParamPrefix}_${regionField}`
  }

  if (input[regionField] !== undefined) {
    const breakdown = validRegion(input[regionField] as string)

    if (breakdown != null) {
      newInput[chrField] = breakdown[1]

      if (singleFieldRangeQueryDB !== null) {
        newInput[singleFieldRangeQueryDB] = `range:${breakdown[2]}-${breakdown[3]}`
      } else {
        newInput.intersect = `${startField}-${endField}:${breakdown[2]}-${breakdown[3]}`
      }

      // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
      delete newInput[regionField]
    } else {
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: 'Region format invalid. Please use the format as the example: "chr2:12345-54321"'
      })
    }
  }

  return newInput
}

// takes a list of ids and builds a dictionary where keys are ids and values are simplified objects from database
export async function verboseItems (ids: string[], schema: Record<string, any>): Promise<Record<string, any>> {
  const router = new RouterFilterBy(schema)
  const verboseQuery = `
    FOR record in ${router.dbCollectionName}
    FILTER record._id in ['${Array.from(ids).join('\',\'')}']
    RETURN {
      ${new RouterFilterBy(schema).simplifiedDbReturnStatements}
    }`

  const objs = await (await db.query(verboseQuery)).all()

  if (objs.length > 0) {
    const items: Record<string, any> = {}

    objs.forEach((obj: Record<string, any>) => {
      items[obj._id] = obj
    })

    return items
  } else {
    return {}
  }
}

// Generates aql RETURN statement, for the `return` list in a schema
// Example:
// for return statement based on schema: "return: _id, pos, name"
// outputs: "{ id: record._key, pos: record['pos:long'], name: record.name }"
export function getDBReturnStatements (
  schema: configType
): string {
  const properties = schema.properties as Record<string, string>
  const schemaReturns = (schema.accessible_via as Record<string, string>).return.split(',').map((item: string) => item.trim())

  let returns: string[] = []
  schemaReturns.forEach((field: string) => {
      if (field === '_id') {
        returns.push('id: record._key')
      } else if (properties[field] === 'int') {
        returns.push(`'${field}': record['${field}:long']`)
      } else {
        returns.push(`'${field}': record['${field}']`)
      }
    })

  return returns.join(', ')
}

// Generates aql FILTER parameters based on queryParams received from user
// Example:
// for the schema: 'coding_variants' and queryParams: { aaapos: "intersect:123-321", gene_name: "ACT1" }
// outpus: "record['aaapos:int'] >= 123 AND record['aaapos:int'] <= 321 AND record.gene_name == 'ACT1'"
export function getFilterStatements (
  schema: configType,
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
      const filterByRangeFields = (schema.accessible_via as Record<string, string>).filter_by_range?.split(',').map((item: string) => item.trim()) || []

      // 'interesect' is a reserved parameter for intersectional region search
      // 'annotation.freq' is a special case for variant data
      if (filterByRangeFields.includes(element) || element === 'intersect' || element.startsWith('annotations.freq')) {
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
        } else if ((schema.properties as Record<string, string>)[element] === 'array') {
          dbFilterBy.push(`'${queryParams[element] as string | number}' in record.${element}`)
        } else if ((schema.properties as Record<string, string>)[element] === 'int') {
          dbFilterBy.push(`record['${element}:long'] == ${queryParams[element] as string | number}`)
        } else {
          dbFilterBy.push(`record.${element} == '${queryParams[element] as string | number}'`)
        }
      }
    }
  })

  return dbFilterBy.join(` ${joinBy} `) // default: 'and'
}
