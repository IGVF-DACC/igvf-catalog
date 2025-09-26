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

// currently supports: gene, protein, and disease
async function autocompleteQuery (input: paramsFormatType): Promise<any[]> {
  const term = (input.term as string).toUpperCase()

  const query = `
    LET genes = (FOR gene in genes
    FILTER STARTS_WITH(gene.name, "${term}")
    RETURN { type: "gene", term: gene.name, uri: CONCAT("/genes/", gene._key) })

    LET proteins = (FOR protein in proteins
    FILTER STARTS_WITH(protein.names[0], "${term}")
    RETURN { type: "protein", term: protein.names[0], uri: CONCAT("/proteins/", protein._key) })

    FOR result IN UNION_DISTINCT(genes, proteins)
    SORT LENGTH(result.term) ASC
    LIMIT ${input.page as number * PAGE_SIZE}, ${PAGE_SIZE}
    RETURN result
  `

  return await ((await db.query(query)).all())
}

const autocomplete = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/autocomplete', description: descriptions.autocomplete } })
  .input(autocompleteQueryFormat)
  .output(z.array(autocompleteFormat))
  .query(async ({ input }) => await autocompleteQuery(input))

export const autocompleteRouters = {
  autocomplete
}
