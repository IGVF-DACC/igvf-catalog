import { TRPCError } from '@trpc/server'
import { RouterFilterBy } from '../genericRouters/routerFilterBy'
import { db } from '../../database'

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
export async function verboseItems (collection: string, ids: string[], schema: Record<string, any>): Promise<Record<string, any>> {
  const verboseQuery = `
    FOR record in ${collection}
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
