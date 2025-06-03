import { metaAPIOutput, metaAPIMiddleware } from '../meta'
import { z } from 'zod'
import { Context } from '../trpc'

describe('metaAPIOutput', () => {
  test('should return a valid schema with meta and data', () => {
    const dataSchema = z.array(z.object({ id: z.string(), name: z.string() }))
    const schema = metaAPIOutput(dataSchema)

    const validData = {
      meta: {
        count: 2,
        query: '/test',
        next: '/test?page=2'
      },
      data: [
        { id: '1', name: 'Item 1' },
        { id: '2', name: 'Item 2' }
      ]
    }

    expect(schema.safeParse(validData).success).toBe(true)
  })

  test('should allow data without meta when using `.or(data)`', () => {
    const dataSchema = z.array(z.object({ id: z.string(), name: z.string() }))
    const schema = metaAPIOutput(dataSchema)

    const validData = [
      { id: '1', name: 'Item 1' },
      { id: '2', name: 'Item 2' }
    ]

    expect(schema.safeParse(validData).success).toBe(true)
  })
})

describe('metaAPIMiddleware', () => {
  afterEach(() => {
    jest.restoreAllMocks()
  })

  test('should add meta information to the response with next page if available', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue([{ id: '3', name: 'Item 3' }])
    })

    const mockContext: Context = {
      requestId: 'mock-request-id',
      origin: 'http://localhost:3000',
      originalUrl: '/test?page=1'
    }

    const mockNext = jest.fn().mockResolvedValue({
      ok: true,
      data: [{ id: '1', name: 'Item 1' }, { id: '2', name: 'Item 2' }]
    })

    const result = await metaAPIMiddleware({
      ctx: mockContext,
      next: mockNext,
      path: 'mockProcedure',
      input: {},
      type: 'query',
      rawInput: {},
      meta: undefined
    })

    expect(mockNext).toHaveBeenCalled()
    expect(result.ok).toBe(true)

    const data = Object.entries(result).find(([k]) => k === 'data')?.[1]
    expect(data.meta).toEqual({
      count: 2,
      query: '/test?page=1',
      next: 'http://localhost:3000/test?page=2'
    })
    expect(data.data).toEqual([{ id: '1', name: 'Item 1' }, { id: '2', name: 'Item 2' }])
  })

  test('should add meta information to the response with empty next page is empty', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue([])
    })

    const mockContext: Context = {
      requestId: 'mock-request-id',
      origin: 'http://localhost:3000',
      originalUrl: '/test?page=1'
    }

    const mockNext = jest.fn().mockResolvedValue({
      ok: true,
      data: [{ id: '1', name: 'Item 1' }, { id: '2', name: 'Item 2' }]
    })

    const result = await metaAPIMiddleware({
      ctx: mockContext,
      next: mockNext,
      path: 'mockProcedure',
      input: {},
      type: 'query',
      rawInput: {},
      meta: undefined
    })

    expect(mockNext).toHaveBeenCalled()
    expect(result.ok).toBe(true)

    const data = Object.entries(result).find(([k]) => k === 'data')?.[1]
    expect(data.meta).toEqual({
      count: 2,
      query: '/test?page=1',
      next: ''
    })
    expect(data.data).toEqual([{ id: '1', name: 'Item 1' }, { id: '2', name: 'Item 2' }])
  })

  test('should not add meta information and return result if meta=false', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue([])
    })

    const mockContext: Context = {
      requestId: 'mock-request-id',
      origin: 'http://localhost:3000',
      originalUrl: '/test?page=1&meta=false'
    }

    const mockNext = jest.fn().mockResolvedValue({
      ok: true,
      data: [{ id: '1', name: 'Item 1' }, { id: '2', name: 'Item 2' }]
    })

    const result = await metaAPIMiddleware({
      ctx: mockContext,
      next: mockNext,
      path: 'mockProcedure',
      input: {},
      type: 'query',
      rawInput: {},
      meta: undefined
    })

    expect(mockNext).toHaveBeenCalled()
    expect(result.ok).toBe(true)

    const data = Object.entries(result).find(([k]) => k === 'data')?.[1]
    expect(data).toEqual([{ id: '1', name: 'Item 1' }, { id: '2', name: 'Item 2' }])
    expect(data.meta).toBeUndefined()
  })

  test('should return empty next page if fetch fails', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Fetch error'))

    const mockContext: Context = {
      requestId: 'mock-request-id',
      origin: 'http://localhost:3000',
      originalUrl: '/test?page=1'
    }

    const mockNext = jest.fn().mockResolvedValue({
      ok: true,
      data: [{ id: '1', name: 'Item 1' }, { id: '2', name: 'Item 2' }]
    })

    const result = await metaAPIMiddleware({
      ctx: mockContext,
      next: mockNext,
      path: 'mockProcedure',
      input: {},
      type: 'query',
      rawInput: {},
      meta: undefined
    })

    expect(mockNext).toHaveBeenCalled()
    expect(result.ok).toBe(true)

    const data = Object.entries(result).find(([k]) => k === 'data')?.[1]
    expect(data.meta).toEqual({
      count: 2,
      query: '/test?page=1',
      next: ''
    })
    expect(data.data).toEqual([{ id: '1', name: 'Item 1' }, { id: '2', name: 'Item 2' }])
  })
})
