import { TRPCError } from '@trpc/server'

type paramsFormatType = Record<string, string | number | undefined>

function validRegion (region: string): string[] | null {
  const regex: RegExp = /(chr\w):(\d*)-(\d*)/

  if (regex.test(region)) {
    const breakdown = regex.exec(region)
    if (breakdown === null || breakdown.length < 4) {
      return null
    }
    return breakdown
  }

  return null
}

export function preProcessRegionParam (input: paramsFormatType): paramsFormatType {
  const newInput = input

  if (input.region !== undefined) {
    const breakdown = validRegion(input.region as string)

    if (breakdown != null) {
      newInput.chr = breakdown[1]
      newInput.start = 'gte:' + breakdown[2]
      newInput.end = 'lte:' + breakdown[3]

      delete newInput.region
    } else {
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: 'Region format invalid. Please use the format as the example: "chr2:12345-54321"'
      })
    }
  }

  return newInput
}
