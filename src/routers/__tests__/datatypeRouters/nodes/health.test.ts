import { healthRouters } from '../../../datatypeRouters/nodes/health'
import * as dbModule from '../../../../database'
import * as envModule from '../../../../env'

jest.mock('../../../../database')
jest.mock('../../../../env')

describe('healthRouters.health', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  beforeEach(() => {
    envModule.envData.database.connectionUri = 'mock-db-uri'
  })

  it('returns OK status when DB query succeeds', async () => {
    jest.spyOn(dbModule.db, 'query').mockResolvedValue({
      all: jest.fn().mockResolvedValue([1])
    } as any)

    const result = await healthRouters.health({
      input: undefined,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: undefined
    }) as {
      status: string
      arangodb: string
      database_url: string
    }

    expect(result.status).toBe('OK')
    expect(result.arangodb).toBe('OK')
    expect(result.database_url).toBe('mock-db-uri')
  })

  it('returns ERROR status when DB query fails', async () => {
    jest.spyOn(dbModule.db, 'query').mockRejectedValue(new Error('Connection failed'))

    const result = await healthRouters.health({
      input: undefined,
      ctx: {},
      type: 'query',
      path: '',
      rawInput: undefined
    }) as {
      status: string
      arangodb: string
      database_url: string
    }

    expect(result.status).toBe('ERROR')
    expect(result.arangodb).toContain('ERROR: Connection failed')
    expect(result.database_url).toBe('mock-db-uri')
  })
})
