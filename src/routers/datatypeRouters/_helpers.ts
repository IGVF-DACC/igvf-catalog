import { TRPCError } from '@trpc/server'

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
  let regionName = 'region'
  if (regionParamPrefix !== '') {
    chrField = `${regionParamPrefix}_chr`
    startField = `${regionParamPrefix}_start`
    endField = `${regionParamPrefix}_end`
    regionName = `${regionParamPrefix}_region`
  }

  if (input[regionName] !== undefined) {
    const breakdown = validRegion(input[regionName] as string)

    if (breakdown != null) {
      newInput[chrField] = breakdown[1]

      if (singleFieldRangeQueryDB !== null) {
        newInput[singleFieldRangeQueryDB] = `range:${breakdown[2]}-${breakdown[3]}`
      } else {
        newInput[startField] = 'gte:' + breakdown[2]
        newInput[endField] = 'lte:' + breakdown[3]
      }

      // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
      delete newInput[regionName]
    } else {
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: 'Region format invalid. Please use the format as the example: "chr2:12345-54321"'
      })
    }
  }

  return newInput
}
