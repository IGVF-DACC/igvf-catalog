import { openApiDocument } from '../../../openapi'
import { pagingParamsFormat } from '../../datatypeRouters/params'

jest.mock('../../../database')

describe('pagingParamsFormat', () => {
  it('defaults page to 0 and leaves limit undefined', () => {
    expect(pagingParamsFormat.parse({})).toEqual({ page: 0 })
  })

  it('accepts a non-negative integer page and a positive integer limit', () => {
    expect(pagingParamsFormat.parse({ page: 2, limit: 3 })).toEqual({ page: 2, limit: 3 })
  })

  it.each([
    { page: -1 },
    { page: 0.5 },
    { limit: -1 },
    { limit: 0 },
    { limit: 2.5 }
  ])('rejects %j', input => {
    expect(pagingParamsFormat.safeParse(input).success).toBe(false)
  })
})

describe('OpenAPI paging parameters', () => {
  const pagingParams: Array<{ path: string, name: string, schema: any }> = []
  for (const [path, item] of Object.entries(openApiDocument.paths ?? {})) {
    for (const operation of Object.values(item as Record<string, any>)) {
      for (const param of (operation?.parameters ?? []) as any[]) {
        if (param.in === 'query' && (param.name === 'page' || param.name === 'limit')) {
          pagingParams.push({ path, name: param.name, schema: param.schema })
        }
      }
    }
  }

  it('finds paging parameters to check', () => {
    expect(pagingParams.filter(p => p.name === 'page').length).toBeGreaterThan(50)
    expect(pagingParams.filter(p => p.name === 'limit').length).toBeGreaterThan(50)
  })

  it('types every page as a non-negative integer', () => {
    const invalid = pagingParams
      .filter(p => p.name === 'page')
      .filter(p => p.schema.type !== 'integer' || p.schema.minimum !== 0 || p.schema.exclusiveMinimum !== undefined)
      .map(p => p.path)
    expect(invalid).toEqual([])
  })

  it('types every limit as a positive integer', () => {
    const isPositive = (schema: any): boolean =>
      (schema.minimum === 0 && schema.exclusiveMinimum === true) || schema.exclusiveMinimum === 0 || schema.minimum >= 1
    const invalid = pagingParams
      .filter(p => p.name === 'limit')
      .filter(p => p.schema.type !== 'integer' || !isPositive(p.schema))
      .map(p => p.path)
    expect(invalid).toEqual([])
  })
})
