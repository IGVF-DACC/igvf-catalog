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
  name: z.string(),
  uri: z.string()
})

// currently supports: gene, protein, and disease
async function autocompleteQuery (input: paramsFormatType): Promise<any[]> {
  const term = (input.term as string).toUpperCase()

  const query = `
    LET genesByName = (
      FOR gene IN genes
        FILTER STARTS_WITH(UPPER(gene.name), "${term}")
        SORT LENGTH(gene.name) ASC
        LIMIT ${input.page as number * PAGE_SIZE}, ${PAGE_SIZE}
        RETURN { type: "gene", term: gene.name, name: gene.name, uri: CONCAT("/genes/", gene._key) }
    )

    LET genesBySynonym = (
      FOR gene IN genes
        FOR synonym IN (gene.synonyms || [])
          FILTER STARTS_WITH(UPPER(synonym), "${term}")
            AND NOT CONTAINS(synonym, " ")
            AND NOT STARTS_WITH(gene.name, "${term}") // avoid duplicates with genesByName
          SORT LENGTH(synonym) ASC
          LIMIT ${input.page as number * PAGE_SIZE}, ${PAGE_SIZE}
          RETURN { type: "gene", term: synonym, name: gene.name, uri: CONCAT("/genes/", gene._key) }
    )

    RETURN UNION(genesByName, genesBySynonym)
  `
  const results = await ((await db.query(query)).all())

  if (results.length > 0) {
    return results[0]
  }

  return []
}

const autocomplete = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/autocomplete', description: descriptions.autocomplete } })
  .input(autocompleteQueryFormat)
  .output(z.array(autocompleteFormat))
  .query(async ({ input }) => await autocompleteQuery(input))

export const autocompleteRouters = {
  autocomplete
}
