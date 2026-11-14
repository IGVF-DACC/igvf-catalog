import { descriptions } from '../descriptions'
import { z } from 'zod'
import { TRPCError } from '@trpc/server'
import { db } from '../../../database'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, preProcessRegionParam, withHgncPrefix } from '../_helpers'
import { getSchema } from '../schema'
import { geneFormat } from '../nodes/genes'
import { geneProgramFormat, geneProgramSchema } from '../nodes/gene_programs'
import { contextFilters, documentId, programContextFormat, programContextQuery, programNumericFilter, programPagination } from '../gene_programs_shared'

const schema = getSchema('data/schemas/edges/genes_gene_programs.GenePrograms.json')
const geneSchema = getSchema('data/schemas/nodes/genes.GencodeGene.json')
const queryFormat = programContextQuery.merge(programPagination).extend({
  gene_id: z.string().trim().min(1).optional(),
  gene_name: z.string().trim().min(1).optional(),
  hgnc_id: z.string().trim().min(1).optional(),
  synonym: z.string().trim().min(1).optional(),
  region: z.string().trim().optional(),
  gene_program_id: z.string().trim().min(1).optional().describe('Catalog program key including its defining file accession, or document ID.'),
  label: z.enum(['gene program membership', 'gene program regulation']).optional(),
  score: programNumericFilter.optional(),
  log2FC: programNumericFilter.optional(),
  neg_log10_pvalue_adj: programNumericFilter.optional(),
  significant: z.enum(['true', 'false']).optional(),
  verbose: z.enum(['true', 'false']).default('false')
})
const outputFormat = programContextFormat.extend({
  _id: z.string(),
  gene: z.string().or(geneFormat),
  gene_program: z.string().or(geneProgramFormat),
  name: z.string(),
  inverse_name: z.string(),
  score: z.number().nullish(),
  genomic_elements: z.array(z.string()).nullish(),
  log2FC: z.number().nullish(),
  test_statistic: z.number().nullish(),
  neg_log10_pvalue: z.number().nullish(),
  neg_log10_pvalue_adj: z.number().nullish(),
  reference_group: z.string().nullish(),
  fdr_method: z.string().nullish(),
  significant: z.boolean().nullish()
})

async function findRelationships (input: z.infer<typeof queryFormat>, reverse: boolean): Promise<any[]> {
  const geneFilter = getFilterStatements(geneSchema, preProcessRegionParam({
    _key: input.gene_id === undefined ? undefined : documentId('genes', input.gene_id).split('/')[1],
    name: input.gene_name,
    hgnc: input.hgnc_id === undefined ? undefined : withHgncPrefix(input.hgnc_id),
    synonyms: input.synonym,
    region: input.region
  })).replaceAll('record', 'gene')
  if (reverse ? input.gene_program_id === undefined : !geneFilter) {
    throw new TRPCError({ code: 'BAD_REQUEST', message: reverse ? 'gene_program_id is required.' : 'At least one gene identifier is required.' })
  }
  const filters = [getFilterStatements(schema, {
    ...contextFilters(input),
    _to: input.gene_program_id === undefined ? undefined : documentId('gene_programs', input.gene_program_id),
    label: input.label,
    score: input.score,
    log2FC: input.log2FC,
    neg_log10_pvalue_adj: input.neg_log10_pvalue_adj,
    significant: input.significant === undefined ? undefined : input.significant === 'true'
  })]
  if (geneFilter) filters.push('record._from == gene._id')
  for (const field of ['score', 'log2FC', 'neg_log10_pvalue_adj'] as const) {
    if (input[field] !== undefined) filters.push(`IS_NUMBER(record.${field})`)
  }
  const verboseGene = `(FOR other IN genes FILTER other._id == record._from RETURN {${getDBReturnStatements(geneSchema).replaceAll('record', 'other')}})[0]`
  const verboseProgram = `(FOR other IN gene_programs FILTER other._id == record._to RETURN {${getDBReturnStatements(geneProgramSchema).replaceAll('record', 'other')}})[0]`
  const query = `${geneFilter ? `FOR gene IN genes FILTER ${geneFilter}` : ''}
    FOR record IN genes_gene_programs
    FILTER ${filters.filter(Boolean).join(' AND ')}
    SORT record._key
    LIMIT ${input.page * input.limit}, ${input.limit}
    RETURN {${getDBReturnStatements(schema, false, '', ['name', 'inverse_name'])}, _id: record._id,
      name: record.${reverse ? 'inverse_name' : 'name'},
      inverse_name: record.${reverse ? 'name' : 'inverse_name'},
      gene: ${input.verbose === 'true' ? verboseGene : 'record._from'},
      gene_program: ${input.verbose === 'true' ? verboseProgram : 'record._to'}}`
  return await (await db.query(query)).all()
}

const geneProgramsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/gene-programs', description: descriptions.genes_gene_programs } })
  .input(queryFormat).output(z.array(outputFormat))
  .query(async ({ input }) => await findRelationships(input, false))
const genesFromGenePrograms = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/gene-programs/genes', description: descriptions.gene_programs_genes } })
  .input(queryFormat).output(z.array(outputFormat))
  .query(async ({ input }) => await findRelationships(input, true))

export const genesGeneProgramsRouters = { geneProgramsFromGenes, genesFromGenePrograms }
