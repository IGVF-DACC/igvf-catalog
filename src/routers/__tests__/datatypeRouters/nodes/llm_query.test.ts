import { llmQueryRouters } from '../../../datatypeRouters/nodes/llm_query'
import * as envModule from '../../../../env'
import { TRPCError } from '@trpc/server'

jest.mock('../../../../env')

// Store the original fetch
const originalFetch = global.fetch

describe('llmQueryRouters.llmQuery', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Make fetch writable for mocking in Node 20+
    Object.defineProperty(global, 'fetch', {
      writable: true,
      configurable: true,
      value: originalFetch
    })
  })

  beforeEach(() => {
    envModule.envData.catalog_llm_query_service_url = 'https://mock-llm-service/query'
  })

  afterEach(() => {
    jest.clearAllTimers()
    jest.useRealTimers()
    // Restore original fetch
    Object.defineProperty(global, 'fetch', {
      writable: false,
      configurable: true,
      value: originalFetch
    })
  })

  it('returns answer for successful response (verbose false)', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({ result: '42' })
    }) as any

    const input = { query: 'What is the answer?', password: 'pw', verbose: 'false' }
    const result = await llmQueryRouters.llmQuery({
      input,
      ctx: {},
      type: 'mutation',
      path: '',
      rawInput: input
    })
    expect(result).toEqual({ query: 'What is the answer?', answer: '42' })
  })

  it('returns verbose fields for successful response (verbose true)', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({
        result: '42',
        aql_query: 'FOR x IN y RETURN x',
        aql_result: [1, 2, 3]
      })
    }) as any

    const input = { query: 'What is the answer?', password: 'pw', verbose: 'true' }
    const result = await llmQueryRouters.llmQuery({
      input,
      ctx: {},
      type: 'mutation',
      path: '',
      rawInput: input
    })
    expect(result).toEqual({
      query: 'What is the answer?',
      aql: 'FOR x IN y RETURN x',
      aql_result: [1, 2, 3],
      answer: '42'
    })
  })

  it('throws BAD_REQUEST if response not ok', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      json: jest.fn().mockResolvedValue({ error: 'Bad query' })
    }) as any

    const input = { query: 'bad', password: 'pw', verbose: 'false' }
    await expect(
      llmQueryRouters.llmQuery({
        input,
        ctx: {},
        type: 'mutation',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })

  it('throws BAD_REQUEST for empty query', async () => {
    const input = { query: '', password: 'pw', verbose: 'false' }
    await expect(
      llmQueryRouters.llmQuery({
        input,
        ctx: {},
        type: 'mutation',
        path: '',
        rawInput: input
      })
    ).rejects.toThrow(TRPCError)
  })
})
