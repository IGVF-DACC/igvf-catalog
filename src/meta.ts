import { z, ZodSchema } from 'zod'
import { t } from './trpc'

export function metaAPIOutput (data: z.ZodTypeAny): ZodSchema {
  return z.object({
    meta: z.object({
      count: z.number(),
      query: z.string(),
      next: z.string()
    }),
    data
  }).or(data)
}

export const metaAPIMiddleware = t.middleware(async ({ ctx, next }) => {
  const result = await next()

  const url = ctx.originalUrl
  const parsedUrl = new URL(url, ctx.origin)

  if (!result.ok || parsedUrl.searchParams.get('meta') === 'false') {
    return result
  }

  const currentPage = parseInt(parsedUrl.searchParams.get('page') ?? '0', 10)

  parsedUrl.searchParams.set('page', (currentPage + 1).toString())
  let nextUrl = parsedUrl.toString()

  try {
    // no verbose to speed up next query
    parsedUrl.searchParams.set('verbose', 'false')
    parsedUrl.searchParams.set('meta', 'false')
    const response = await fetch(parsedUrl.toString())

    // fetch next page, if it exists, we set nextUrl to the next page URL, otherwise, we set it to an empty string
    if (response.ok) {
      const nextPageData = await response.json()
      const nextPageLength = Array.isArray(nextPageData) ? nextPageData.length : 1

      if (nextPageLength < 1) {
        nextUrl = ''
      }
    } else {
      nextUrl = ''
    }
  } catch (err) {
    console.error(`Error fetching next page from ${parsedUrl.toString()}:`, err)
    nextUrl = ''
  }

  const dataCount = Array.isArray(result.data) ? result.data.length : 1

  return {
    ...result,
    data: {
      meta: {
        count: dataCount,
        query: url,
        next: nextUrl
      },
      data: result.data
    }
  }
})
