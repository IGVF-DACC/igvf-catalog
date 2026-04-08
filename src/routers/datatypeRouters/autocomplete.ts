import { publicProcedure } from '../../trpc'
import { paramsFormatType } from './_helpers'
import { z } from 'zod'
import { db } from '../../database'
import { descriptions } from './descriptions'

const PAGE_SIZE = 500

const autocompleteQueryFormat = z.object({
  term: z.string().trim(),
  page: z.number().default(0).optional()
})

const autocompleteFormat = z.object({
  term: z.string(),
  type: z.string(),
  uri: z.string()
})

// currently supports genes only
async function autocompleteQuery (input: paramsFormatType): Promise<any[]> {
  const term = (input.term as string).toUpperCase()

  const query = `
    FOR gene in genes
    FILTER STARTS_WITH(gene.name, "${term}")
    SORT LENGTH(gene.name) ASC
    LIMIT ${input.page as number * PAGE_SIZE}, ${PAGE_SIZE}
    RETURN { type: "gene", term: gene.name, uri: CONCAT("/genes/", gene._key) }
  `
  const results = await ((await db.query(query)).all())
  return results
}

const autocomplete = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/autocomplete', description: descriptions.autocomplete } })
  .input(autocompleteQueryFormat)
  .output(z.array(autocompleteFormat))
  .query(async ({ input }) => await autocompleteQuery(input))

export const autocompleteRouters = {
  autocomplete
}
