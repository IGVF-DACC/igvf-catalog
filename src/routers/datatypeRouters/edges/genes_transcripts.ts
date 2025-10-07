import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { transcriptFormat } from '../nodes/transcripts'
import { geneFormat, geneSearch } from '../nodes/genes'
import { proteinByIDQuery, proteinFormat } from '../nodes/proteins'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonEdgeParamsFormat, genesCommonQueryFormat, proteinsCommonQueryFormat, transcriptsCommonQueryFormat } from '../params'

const MAX_PAGE_SIZE = 100

const genesTranscriptsFormat = z.object({
  source: z.string().optional(),
  source_url: z.string().optional(),
  version: z.string().optional(),
  gene: z.string().or(geneFormat).optional(),
  transcript: z.string().or(transcriptFormat).optional(),
  name: z.string()
})
const genesProteinsFormat = z.object({
  gene: z.string().or(geneFormat).optional(),
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

function validateGeneInput (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['gene_id', 'hgnc_id', 'gene_name', 'alias'].includes(item))
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one gene property must be defined.'
    })
  }
}

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
      LET proteins = ${proteinByIDQuery(input.protein_id as string)}

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
    return await (await db.query(query)).all()
  }

  input.names = input.protein_name
  input.full_names = input.full_name
  delete input.protein_name
  delete input.full_name

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

  return await (await db.query(query)).all()
}

async function findProteinsFromGenesSearch (input: paramsFormatType): Promise<any[]> {
  validateGeneInput(input)
  let geneSchema = geneSchemaHuman
  if (input.organism === 'Mus musculus') {
    geneSchema = geneSchemaMouse
  }
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { gene_id, hgnc_id, gene_name: name, alias, organism } = input
  const geneInput: paramsFormatType = { gene_id, hgnc_id, name, alias, organism, page: 0 }
  delete input.hgnc_id
  delete input.gene_name
  delete input.alias
  delete input.organism
  const genes = await geneSearch(geneInput)
  const geneIDs = genes.map(gene => `${geneSchema.db_collection_name as string}/${gene._id as string}`)

  const verboseQuery = `
  FOR otherRecord IN ${proteinSchema.db_collection_name as string}
  FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
  RETURN {${getDBReturnStatements(proteinSchema).replaceAll('record', 'otherRecord')}}
  `
  const query = `
    LET geneTranscriptEdges = (
      FOR record IN ${genesTranscriptsSchema.db_collection_name as string}
      FILTER record._from IN ${JSON.stringify(geneIDs)}
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
  return await (await db.query(query)).all()
}

async function findTranscriptsFromGeneSearch (input: paramsFormatType): Promise<any[]> {
  validateGeneInput(input)
  let geneSchema = geneSchemaHuman
  let transcriptSchema = transcriptSchemaHuman
  if (input.organism === 'Mus musculus') {
    geneSchema = geneSchemaMouse
    transcriptSchema = transcriptSchemaMouse
  }
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { gene_id, hgnc_id, gene_name: name, alias, organism } = input
  const geneInput: paramsFormatType = { gene_id, hgnc_id, name, alias, organism, page: 0 }
  delete input.hgnc_id
  delete input.gene_name
  delete input.alias
  delete input.organism
  const genes = await geneSearch(geneInput)
  const geneIDs = genes.map(gene => `${geneSchema.db_collection_name as string}/${gene._id as string}`)

  const verboseQuery = `
    FOR otherRecord IN ${transcriptSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(transcriptSchema).replaceAll('record', 'otherRecord')}}
  `

  const query = `

    FOR record IN ${genesTranscriptsSchema.db_collection_name as string}
      FILTER record._from IN ${JSON.stringify(geneIDs)}
      SORT record.chr
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'gene': record._from,
        'transcript': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._to'},
        ${getDBReturnStatements(genesTranscriptsSchema)},
        'name': record.name
      }
  `
  return await (await db.query(query)).all()
}

async function findGenesFromTranscriptSearch (input: paramsFormatType): Promise<any[]> {
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
        ${getDBReturnStatements(genesTranscriptsSchema)},
        'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
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
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'transcript': record._to,
        'gene': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._from'},
        ${getDBReturnStatements(genesTranscriptsSchema)},
        'name': record.name,
        'inverse_name': record.inverse_name
      }
  `
  return await (await db.query(query)).all()
}

const transcriptsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/transcripts', description: descriptions.genes_transcripts } })
  .input(genesCommonQueryFormat.merge(commonEdgeParamsFormat))
  .output(z.array(genesTranscriptsFormat))
  .query(async ({ input }) => await findTranscriptsFromGeneSearch(input))

const genesFromTranscripts = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/transcripts/genes', description: descriptions.transcripts_genes } })
  .input(transcriptsCommonQueryFormat.merge(commonEdgeParamsFormat))
  .output(z.array(genesTranscriptsFormat))
  .query(async ({ input }) => await findGenesFromTranscriptSearch(input))

const proteinsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/proteins', description: descriptions.genes_proteins } })
  .input(genesCommonQueryFormat.merge(commonEdgeParamsFormat))
  .output(z.array(genesProteinsFormat))
  .query(async ({ input }) => await findProteinsFromGenesSearch(input))

const genesFromProteins = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/proteins/genes', description: descriptions.proteins_genes } })
  .input(proteinsCommonQueryFormat.merge(commonEdgeParamsFormat))
  .output(z.array(genesProteinsFormat))
  .query(async ({ input }) => await findGenesFromProteins(input))

export const genesTranscriptsRouters = {
  transcriptsFromGenes,
  genesFromTranscripts,
  proteinsFromGenes,
  genesFromProteins
}
