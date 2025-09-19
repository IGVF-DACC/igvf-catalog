import { healthRouters } from '../../../datatypeRouters/nodes/health'

describe('healthRouters.health', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns OK when application is up', async () => {
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

    expect(result.status).toBe('ok')
  })
})
