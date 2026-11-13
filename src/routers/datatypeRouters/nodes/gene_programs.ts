import { descriptions } from '../descriptions'
import { z } from 'zod/v4'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements } from '../_helpers'
import { getSchema } from '../schema'
import { contextFilters, documentId, programContextFormat, programContextQuery, programPagination } from '../gene_programs_shared'

export const geneProgramSchema = getSchema('data/schemas/nodes/gene_programs.GenePrograms.json')
export const geneProgramFormat = programContextFormat.extend({
  _id: z.string(),
  name: z.string(),
  program_id: z.string(),
  reported_gene_count: z.number().int()
})

const queryFormat = programContextQuery.merge(programPagination).extend({
  id: z.string().trim().min(1).optional().describe('Catalog program key or gene_programs/key document ID.'),
  program_id: z.string().trim().min(1).optional().describe('File-local program identifier; combine with files_fileset to disambiguate.'),
  name: z.string().trim().min(1).optional()
})

const genePrograms = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/gene-programs', description: descriptions.gene_programs } })
  .input(queryFormat)
  .output(z.array(geneProgramFormat))
  .query(async ({ input }) => {
    const filters = getFilterStatements(geneProgramSchema, {
      ...contextFilters(input),
      _key: input.id === undefined ? undefined : documentId('gene_programs', input.id).split('/')[1],
      program_id: input.program_id,
      name: input.name
    })
    const query = `FOR record IN gene_programs
      ${filters ? `FILTER ${filters}` : ''}
      SORT record._key
      LIMIT ${input.page * input.limit}, ${input.limit}
      RETURN {${getDBReturnStatements(geneProgramSchema)}}`
    return await (await db.query(query)).all()
  })

export const geneProgramsRouters = { genePrograms }
