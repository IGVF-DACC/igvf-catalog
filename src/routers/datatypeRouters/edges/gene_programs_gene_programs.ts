import { descriptions } from '../descriptions'
import { z } from 'zod/v4'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, escapeAqlString } from '../_helpers'
import { getSchema } from '../schema'
import { geneProgramFormat, geneProgramSchema } from '../nodes/gene_programs'
import { contextFilters, documentId, programContextFormat, programContextQuery, programNumericFilter, programPagination } from '../gene_programs_shared'

const schema = getSchema('data/schemas/edges/gene_programs_gene_programs.GenePrograms.json')
const queryFormat = programContextQuery.merge(programPagination).extend({
  gene_program_id: z.string().trim().min(1).describe('Catalog program key including defining file accession, or document ID.'),
  associated_gene_program_id: z.string().trim().min(1).optional(),
  pearson_correlation: programNumericFilter.optional(),
  verbose: z.enum(['true', 'false']).default('false')
})
const outputFormat = programContextFormat.extend({
  _id: z.string(),
  gene_program_1: z.string().or(geneProgramFormat),
  gene_program_2: z.string().or(geneProgramFormat),
  name: z.string(),
  inverse_name: z.string(),
  pearson_correlation: z.number().nullable()
})

const geneProgramsGenePrograms = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/gene-programs/gene-programs', description: descriptions.gene_programs_gene_programs } })
  .input(queryFormat).output(z.array(outputFormat))
  .query(async ({ input }) => {
    const id = escapeAqlString(documentId('gene_programs', input.gene_program_id))
    const filters = [`(record._from == '${id}' OR record._to == '${id}')`]
    if (input.associated_gene_program_id !== undefined) {
      const associated = escapeAqlString(documentId('gene_programs', input.associated_gene_program_id))
      filters.push(`((record._from == '${id}' AND record._to == '${associated}') OR (record._to == '${id}' AND record._from == '${associated}'))`)
    }
    filters.push(getFilterStatements(schema, { ...contextFilters(input), pearson_correlation: input.pearson_correlation }))
    if (input.pearson_correlation !== undefined) filters.push('IS_NUMBER(record.pearson_correlation)')
    const verbose = (endpoint: string): string => `(FOR other IN gene_programs FILTER other._id == record.${endpoint} RETURN {${getDBReturnStatements(geneProgramSchema).replaceAll('record', 'other')}})[0]`
    const query = `FOR record IN gene_programs_gene_programs
      FILTER ${filters.filter(Boolean).join(' AND ')}
      SORT record._key
      LIMIT ${input.page * input.limit}, ${input.limit}
      RETURN {${getDBReturnStatements(schema)}, _id: record._id,
        gene_program_1: ${input.verbose === 'true' ? verbose('_from') : 'record._from'},
        gene_program_2: ${input.verbose === 'true' ? verbose('_to') : 'record._to'}}`
    return await (await db.query(query)).all()
  })

export const geneProgramsGeneProgramsRouters = { geneProgramsGenePrograms }
