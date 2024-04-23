import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { transcriptFormat, transcriptsQueryFormat } from '../nodes/transcripts'
import { geneFormat, genesQueryFormat } from '../nodes/genes'
import { proteinFormat, proteinsQueryFormat } from '../nodes/proteins'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'

const MAX_PAGE_SIZE = 100

const genesTranscriptsFormat = z.object({
  source: z.string().optional(),
  source_url: z.string().optional(),
  version: z.string().optional(),
  gene: z.string().or(geneFormat.omit({name: true})).optional(),
  gene_name: z.string().optional(),
  transcript: z.string().or(z.array(transcriptFormat)).optional()
})

const schema = loadSchemaConfig()

const genesTranscriptsSchema = schema['transcribed to']
const transcriptsProteinsSchema = schema['translates to']
const geneSchema = schema.gene
const transcriptSchema = schema.transcript
const proteinSchema = schema.protein

async function findGenesFromProteins (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  if (input.protein_id !== undefined) {
    const query = `
      LET transcripts = (
        FOR record IN ${transcriptsProteinsSchema.db_collection_name}
        FILTER record._to == 'proteins/${decodeURIComponent(input.protein_id as string)}'
        RETURN record._from
      )

      LET genes = (
        FOR record IN ${genesTranscriptsSchema.db_collection_name}
        FILTER record._to IN transcripts
        SORT record.chr
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN DISTINCT DOCUMENT(record._from)
      )

      FOR record in genes
        RETURN {${getDBReturnStatements(geneSchema)}}
    `
    return await (await db.query(query)).all()
  }

  input.name = input.protein_name
  delete input.protein_name

  const filters = getFilterStatements(proteinSchema, preProcessRegionParam(input))
  if (filters === '') {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one query parameter must be defined.'
    })
  }

  const query = `
    LET proteins = (
      FOR record IN ${proteinSchema.db_collection_name}
      FILTER ${filters}
      RETURN record._id
    )

    LET transcripts = (
      FOR record IN ${transcriptsProteinsSchema.db_collection_name}
      FILTER record._to IN proteins
      RETURN record._from
    )

    LET genes = (
      FOR record IN ${genesTranscriptsSchema.db_collection_name}
      FILTER record._to IN transcripts
      SORT record.chr
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN DISTINCT DOCUMENT(record._from)
    )

    FOR record in genes
      RETURN {${getDBReturnStatements(geneSchema)}}
  `
  return await (await db.query(query)).all()
}

async function findProteinsFromGenesSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  if (input.gene_id !== undefined) {
    const query = `
      LET transcripts = (
        FOR record IN ${genesTranscriptsSchema.db_collection_name}
        FILTER record._from == 'genes/${decodeURIComponent(input.gene_id as string)}'
        RETURN record._to
      )

      LET proteins = (
        FOR record IN ${transcriptsProteinsSchema.db_collection_name}
        FILTER record._from IN transcripts
        SORT record.chr
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN DISTINCT DOCUMENT(record._to)
      )

      FOR record IN proteins
        FILTER record != NULL
        RETURN {${getDBReturnStatements(proteinSchema)}}
    `
    return await (await db.query(query)).all()
  }

  input.name = input.gene_name
  delete input.gene_name

  const filters = getFilterStatements(geneSchema, preProcessRegionParam(input))
  if (filters === '') {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one query parameter must be defined.'
    })
  }

  const query = `
    LET primarySources = (
      FOR record IN ${geneSchema.db_collection_name}
      FILTER ${filters}
      RETURN record._id
    )

    LET transcripts = (
      FOR record IN ${genesTranscriptsSchema.db_collection_name}
      FILTER record._from IN primarySources
      RETURN record._to
    )

    LET proteins = (
      FOR record IN ${transcriptsProteinsSchema.db_collection_name}
      FILTER record._from IN transcripts
      SORT record.chr
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN DISTINCT DOCUMENT(record._to)
    )

    FOR record in proteins
      RETURN {${getDBReturnStatements(proteinSchema)}}
  `

  return await (await db.query(query)).all()
}

async function findTranscriptsFromGeneSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const verboseQuery = `
    FOR otherRecord IN ${transcriptSchema.db_collection_name}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(transcriptSchema).replaceAll('record', 'otherRecord')}}
  `

  if (input.gene_id !== undefined) {
    const query = `
      FOR record IN ${genesTranscriptsSchema.db_collection_name}
      FILTER record._from == 'genes/${decodeURIComponent(input.gene_id as string)}'
      SORT record.chr
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'transcript': ${input.verbose === 'true' ? `(${verboseQuery})` : 'record._to'},
        ${getDBReturnStatements(genesTranscriptsSchema)}
      }
    `
    return await (await db.query(query)).all()
  }

  input.name = input.gene_name
  delete input.gene_name

  const filters = getFilterStatements(geneSchema, preProcessRegionParam(input))
  if (filters === '') {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one query parameter must be defined.'
    })
  }

  const query = `
    LET sources = (
      FOR record in ${geneSchema.db_collection_name}
      FILTER ${filters}
      RETURN record._id
    )

    FOR record IN ${genesTranscriptsSchema.db_collection_name}
      FILTER record._from IN sources
      SORT record.chr
      LIMIT ${input.page as number * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN {
        'transcript': ${input.verbose === 'true' ? `(${verboseQuery})` : 'record._to'},
        ${getDBReturnStatements(genesTranscriptsSchema)}
      }
  `
  return await (await db.query(query)).all()
}

async function findGenesFromTranscriptSearch (input: paramsFormatType): Promise<any[]> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const verboseQuery = `
    FOR otherRecord IN ${geneSchema.db_collection_name}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(geneSchema).replaceAll('record', 'otherRecord')}}
  `

  if (input.transcript_id !== undefined) {
    const query = `
      FOR record IN ${genesTranscriptsSchema.db_collection_name}
      FILTER record._to == 'transcripts/${decodeURIComponent(input.transcript_id as string)}'
      SORT record.chr
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'gene': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._from'},
        ${getDBReturnStatements(genesTranscriptsSchema)}
      }
    `
    return await (await db.query(query)).all()
  }

  const filters = getFilterStatements(transcriptSchema, preProcessRegionParam(input))
  if (filters === '') {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one query parameter must be defined.'
    })
  }

  const query = `
    LET targets = (
      FOR record IN ${transcriptSchema.db_collection_name}
      FILTER ${filters}
      RETURN record._id
    )

    FOR record IN ${genesTranscriptsSchema.db_collection_name}
      FILTER record._to IN targets
      SORT record.chr
      LIMIT ${input.page as number * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN {
        'gene': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._from'},
        ${getDBReturnStatements(genesTranscriptsSchema)}
      }
  `
  return await (await db.query(query)).all()
}

const geneQuery = z.object({ gene_name: z.string().optional() }).merge(genesQueryFormat.omit({ organism: true, name: true }))
const proteinQuery = z.object({ protein_name: z.string().optional() }).merge(proteinsQueryFormat.omit({ organism: true, name: true }))

const transcriptsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/transcripts', description: descriptions.genes_transcripts } })
  .input(geneQuery.merge(z.object({ limit: z.number().optional(), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(genesTranscriptsFormat))
  .query(async ({ input }) => await findTranscriptsFromGeneSearch(input))

const genesFromTranscripts = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/transcripts/genes', description: descriptions.transcripts_genes } })
  .input(transcriptsQueryFormat.omit({ organism: true }).merge(z.object({ limit: z.number().optional(), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(genesTranscriptsFormat))
  .query(async ({ input }) => await findGenesFromTranscriptSearch(input))

const proteinsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/proteins', description: descriptions.genes_proteins } })
  .input(geneQuery.merge(z.object({ limit: z.number().optional() })))
  .output(z.array(proteinFormat))
  .query(async ({ input }) => await findProteinsFromGenesSearch(input))

const genesFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/genes', description: descriptions.proteins_genes } })
  .input(proteinQuery.merge(z.object({ limit: z.number().optional() })))
  .output(z.array(geneFormat))
  .query(async ({ input }) => await findGenesFromProteins(input))

export const genesTranscriptsRouters = {
  transcriptsFromGenes,
  genesFromTranscripts,
  proteinsFromGenes,
  genesFromProteins
}
