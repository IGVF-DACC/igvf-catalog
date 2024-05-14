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
  gene: z.string().or(geneFormat.omit({ name: true })).optional(),
  gene_name: z.string().optional(),
  transcript: z.string().or(transcriptFormat).optional()
})
const genesProteinsFormat = z.object({
  gene: z.string().or(geneFormat.omit({ name: true })).optional(),
  protein: z.string().or(proteinFormat).optional()
})
const schema = loadSchemaConfig()

const genesTranscriptsSchema = schema['transcribed to']
const transcriptsProteinsSchema = schema['translates to']
const geneSchemaHuman = schema.gene
const geneSchemaMouse = schema['gene mouse']
const transcriptSchemaHuman = schema.transcript
const transcriptSchemaMouse = schema['transcript mouse']
const proteinSchema = schema.protein

async function findGenesFromProteins (input: paramsFormatType): Promise<any[]> {
  let geneSchema = geneSchemaHuman
  if (input.organism === 'Mus musculus') {
    geneSchema = geneSchemaMouse
  }
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const verboseQuery = `
  FOR otherRecord IN ${geneSchema.db_collection_name as string}
  FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
  RETURN {${getDBReturnStatements(geneSchema).replaceAll('record', 'otherRecord')}}
  `

  if (input.protein_id !== undefined) {
    const query = `
    LET proteins = (
      FOR record IN ${proteinSchema.db_collection_name as string}
      FILTER record._key == '${input.protein_id as string}' and record.organism == '${input.organism as string}'
      RETURN record._id
    )
      LET transcripts = (
        FOR record IN ${transcriptsProteinsSchema.db_collection_name as string}
        FILTER record._to in proteins
        RETURN record._from
      )


      FOR record IN ${genesTranscriptsSchema.db_collection_name as string}
      FILTER record._to IN transcripts
      SORT record.chr
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN DISTINCT {
        'protein': 'proteins/${decodeURIComponent(input.protein_id as string)}',
        'gene': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._from'}
      }
    `
    console.log(query)
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
      FOR record IN ${proteinSchema.db_collection_name as string}
      FILTER ${filters}
      RETURN record._id
    )

    LET transcriptProteinEdges = (
      FOR record IN ${transcriptsProteinsSchema.db_collection_name as string}
      FILTER record._to IN proteins
      RETURN {
        'protein': record._to,
        'transcript': record._from
      }
    )
      FOR edge in transcriptProteinEdges
      FOR record IN ${genesTranscriptsSchema.db_collection_name as string}
      FILTER edge.transcript == record._to
      SORT record.chr
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN DISTINCT {
        'protein': edge.protein,
        'gene':  ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._from'}
      }
  `
  console.log(query)
  return await (await db.query(query)).all()
}

async function findProteinsFromGenesSearch (input: paramsFormatType): Promise<any[]> {
  let geneSchema = geneSchemaHuman
  let geneEndpoint = 'genes/'
  if (input.organism === 'Mus musculus') {
    geneSchema = geneSchemaMouse
    geneEndpoint = 'mm_genes/'
  }
  delete input.organism
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const verboseQuery = `
  FOR otherRecord IN ${proteinSchema.db_collection_name as string}
  FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
  RETURN {${getDBReturnStatements(proteinSchema).replaceAll('record', 'otherRecord')}}
  `

  if (input.gene_id !== undefined) {
    const query = `
      LET transcripts = (
        FOR record IN ${genesTranscriptsSchema.db_collection_name as string}
        FILTER record._from == '${geneEndpoint}${decodeURIComponent(input.gene_id as string)}'
        RETURN record._to
      )

        FOR record IN ${transcriptsProteinsSchema.db_collection_name as string}
        FILTER record._from IN transcripts
        SORT record.chr
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN DISTINCT {
          'gene': '${geneEndpoint}${decodeURIComponent(input.gene_id as string)}',
          'protein': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._to'}
        }

    `
    console.log(query)
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
    LET genes = (
      FOR record IN ${geneSchema.db_collection_name as string}
      FILTER ${filters}
      RETURN record._id
    )

    LET geneTranscriptEdges = (
      FOR record IN ${genesTranscriptsSchema.db_collection_name as string}
      FILTER record._from IN genes
      RETURN {
      'gene': record._from,
      'transcript': record._to
      }
    )

      FOR edge in geneTranscriptEdges
      FOR record IN ${transcriptsProteinsSchema.db_collection_name as string}
      FILTER edge.transcript == record._from
      SORT record.chr
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN DISTINCT {
          'gene': edge.gene,
          'protein': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._to'}
      }
  `
  console.log(query)
  return await (await db.query(query)).all()
}

async function findTranscriptsFromGeneSearch (input: paramsFormatType): Promise<any[]> {
  console.log(input)
  let geneSchema = geneSchemaHuman
  let transcriptSchema = transcriptSchemaHuman
  let geneEndpoint = 'genes/'
  if (input.organism === 'Mus musculus') {
    geneSchema = geneSchemaMouse
    transcriptSchema = transcriptSchemaMouse
    geneEndpoint = 'mm_genes/'
  }
  delete input.organism
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const verboseQuery = `
    FOR otherRecord IN ${transcriptSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(transcriptSchema).replaceAll('record', 'otherRecord')}}
  `

  if (input.gene_id !== undefined) {
    const query = `
      FOR record IN ${genesTranscriptsSchema.db_collection_name as string}
      FILTER record._from == '${geneEndpoint}${decodeURIComponent(input.gene_id as string)}'
      SORT record.chr
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'gene': record._from,
        'transcript': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._to'},
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
      FOR record in ${geneSchema.db_collection_name as string}
      FILTER ${filters}
      RETURN record._id
    )

    FOR record IN ${genesTranscriptsSchema.db_collection_name as string}
      FILTER record._from IN sources
      SORT record.chr
      LIMIT ${input.page as number * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN {
        'gene': record._from,
        'transcript': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._to'},
        ${getDBReturnStatements(genesTranscriptsSchema)}
      }
  `
  console.log(query)
  return await (await db.query(query)).all()
}

async function findGenesFromTranscriptSearch (input: paramsFormatType): Promise<any[]> {
  console.log(input)
  let geneSchema = geneSchemaHuman
  let transcriptSchema = transcriptSchemaHuman
  let transcriptEndpoint = 'transcripts/'
  if (input.organism === 'Mus musculus') {
    geneSchema = geneSchemaMouse
    transcriptSchema = transcriptSchemaMouse
    transcriptEndpoint = 'mm_transcripts/'
  }
  delete input.organism
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const verboseQuery = `
    FOR otherRecord IN ${geneSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(geneSchema).replaceAll('record', 'otherRecord')}}
  `

  if (input.transcript_id !== undefined) {
    const query = `
      FOR record IN ${genesTranscriptsSchema.db_collection_name as string}
      FILTER record._to == '${transcriptEndpoint}${decodeURIComponent(input.transcript_id as string)}'
      SORT record.chr
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'transcript': record._to,
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
      FOR record IN ${transcriptSchema.db_collection_name as string}
      FILTER ${filters}
      RETURN record._id
    )

    FOR record IN ${genesTranscriptsSchema.db_collection_name as string}
      FILTER record._to IN targets
      SORT record.chr
      LIMIT ${input.page as number * QUERY_LIMIT}, ${QUERY_LIMIT}
      RETURN {
        'transcript': record._to,
        'gene': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._from'},
        ${getDBReturnStatements(genesTranscriptsSchema)}
      }
  `
  console.log(query)
  return await (await db.query(query)).all()
}

const geneQuery = z.object({ gene_name: z.string().optional() }).merge(genesQueryFormat.omit({ name: true }))
const proteinQuery = z.object({ protein_name: z.string().optional() }).merge(proteinsQueryFormat.omit({ name: true }))

const transcriptsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/transcripts', description: descriptions.genes_transcripts } })
  .input(geneQuery.merge(z.object({ limit: z.number().optional(), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(genesTranscriptsFormat))
  .query(async ({ input }) => await findTranscriptsFromGeneSearch(input))

const genesFromTranscripts = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/transcripts/genes', description: descriptions.transcripts_genes } })
  .input(transcriptsQueryFormat.merge(z.object({ limit: z.number().optional(), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(genesTranscriptsFormat))
  .query(async ({ input }) => await findGenesFromTranscriptSearch(input))

const proteinsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/proteins', description: descriptions.genes_proteins } })
  .input(geneQuery.merge(z.object({ limit: z.number().optional(), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(genesProteinsFormat))
  .query(async ({ input }) => await findProteinsFromGenesSearch(input))

const genesFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/genes', description: descriptions.proteins_genes } })
  .input(proteinQuery.merge(z.object({ limit: z.number().optional(), verbose: z.enum(['true', 'false']).default('false') })))
  .output(z.array(genesProteinsFormat))
  .query(async ({ input }) => await findGenesFromProteins(input))

export const genesTranscriptsRouters = {
  transcriptsFromGenes,
  genesFromTranscripts,
  proteinsFromGenes,
  genesFromProteins
}
