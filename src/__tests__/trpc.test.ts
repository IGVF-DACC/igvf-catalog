import { createContext, router, publicProcedure, Context } from '../trpc'
import * as trpcExpress from '@trpc/server/adapters/express'
import { v4 as uuid } from 'uuid'

jest.mock('uuid', () => ({
  v4: jest.fn()
}))

describe('trpc.ts', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(uuid as jest.Mock).mockReturnValue('test-request-id')
  })

  test('Context interface and createContext function work correctly', async () => {
    const mockRes = { setHeader: jest.fn() }
    const context: Context = { requestId: 'test-id' }

    expect(context.requestId).toBe('test-id')

    const result = await createContext({ req: {}, res: mockRes } as unknown as trpcExpress.CreateExpressContextOptions)

    expect(result).toEqual({ requestId: 'test-request-id' })
    expect(uuid).toHaveBeenCalledTimes(1)
    expect(mockRes.setHeader).toHaveBeenCalledWith('x-request-id', 'test-request-id')
  })

  test('createContext handles errors gracefully', async () => {
    const mockResWithError = {
      setHeader: jest.fn().mockImplementation(() => {
        throw new Error('Header setting failed')
      })
    }

    await expect(createContext({ req: {}, res: mockResWithError } as unknown as trpcExpress.CreateExpressContextOptions))
      .rejects.toThrow('Header setting failed')
  })

  test('TRPC exports are available and functional', () => {
    expect(router).toBeDefined()
    expect(publicProcedure).toBeDefined()
    expect(publicProcedure.query).toBeDefined()
    expect(publicProcedure.mutation).toBeDefined()
    expect(publicProcedure.subscription).toBeDefined()

    const testRouter = router({
      hello: publicProcedure.query(() => 'Hello World')
    })
    expect(testRouter._def.procedures.hello).toBeDefined()
  })
})
