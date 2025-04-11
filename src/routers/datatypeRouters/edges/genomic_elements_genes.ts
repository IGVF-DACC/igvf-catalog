import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { geneFormat } from '../nodes/genes'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { genomicElementFormat, ZKD_INDEX } from '../nodes/genomic_elements'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonBiosamplesQueryFormat, commonHumanEdgeParamsFormat, commonNodesParamsFormat, genomicElementCommonQueryFormat } from '../params'
import { ontologyFormat, ontologySearch } from '../nodes/ontologies'

const MAX_PAGE_SIZE = 500

const schema = loadSchemaConfig()
const genomicElementToGeneSchema = schema['genomic element to gene expression association']
const genomicElementSchema = schema['genomic element']
const geneSchema = schema.gene

const edgeSources = z.object({
  source: z.enum([
    'ENCODE_EpiRaction',
    'ENCODE-E2G-CRISPR',
    'ENCODE-E2G-DNaseOnly',
    'ENCODE-E2G-Full'
  ]).optional()
})

const genomicElementToGeneFormat = z.object({
  score: z.number().nullable(),
  source: z.string().optional(),
  source_url: z.string().optional(),
  significant: z.boolean().nullish(),
  genomic_element: z.string().or(genomicElementFormat).optional(),
  gene: z.string().or(geneFormat).optional(),
  biosample: z.string().or(ontologyFormat).nullable()
})

const genomicElementFromGeneFormat = z.object({
  gene: z.object({
    name: z.string(),
    id: z.string(),
    start: z.number(),
    end: z.number(),
    chr: z.string()
  }),
  elements: z.array(z.object({
    id: z.string(),
    cell_type: z.string(),
    score: z.number(),
    model: z.string(),
    dataset: z.string(),
    element_type: z.string(),
    element_chr: z.string(),
    element_start: z.number(),
    element_end: z.number()
  }))
}).or(z.object({}))

function edgeQuery (input: paramsFormatType): string {
  let query = ''

  if (input.source !== undefined) {
    query = `record.source == '${input.source as string}'`
    delete input.source
  }

  return query
}

async function getBiosampleIDs (input: paramsFormatType): Promise<string[] | null> {
  let biosampleIDs = null
  if (input.biosample_id !== undefined || input.biosample_name !== undefined || input.biosample_synonyms !== undefined) {
    const biosampleInput: paramsFormatType = {
      term_id: input.biosample_id,
      name: input.biosample_name,
      synonyms: input.biosample_synonyms,
      page: 0
    }
    delete input.biosample_id
    delete input.biosample_name
    delete input.biosample_synonyms
    const biosamples = await ontologySearch(biosampleInput)
    biosampleIDs = biosamples.map((biosample: any) => `ontology_terms/${biosample._id as string}`)
    if (biosampleIDs.length === 0) {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: 'No biosamples found.'
      })
    }
  }
  return biosampleIDs
}

const geneVerboseQuery = `
    FOR otherRecord IN ${geneSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(geneSchema).replaceAll('record', 'otherRecord')}}
  `

const genomicElementVerboseQuery = `
  FOR otherRecord IN ${genomicElementSchema.db_collection_name as string}
  FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
  RETURN {${getDBReturnStatements(genomicElementSchema).replaceAll('record', 'otherRecord')}}
`

async function findGenomicElementsFromGene (input: paramsFormatType): Promise<any[]> {
  if (input.gene_id === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'gene_id must be specified.'
    })
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }
  const query = `
    LET gene = (
      FOR geneRecord IN genes
      FILTER geneRecord._id == 'genes/${input.gene_id as string}'
      RETURN {
        name: geneRecord.name,
        id: geneRecord._id,
        start: geneRecord.start,
        end: geneRecord.end,
        chr: geneRecord.chr
      }
    )[0]

    LET elements = (
      FOR record IN ${genomicElementToGeneSchema.db_collection_name as string}
      FILTER record._to == 'genes/${input.gene_id as string}'
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      LET genomicElement = (
        FOR otherRecord IN ${genomicElementSchema.db_collection_name as string}
        FILTER otherRecord._id == record._from
        RETURN { type: otherRecord.type, chr: otherRecord.chr, start: otherRecord.start, end: otherRecord.end }
      )[0]

      RETURN {
        'id': record._from,
        'cell_type': DOCUMENT(record.biological_context)['name'],
        'score': record.score,
        'model': record.source,
        'dataset': record.source_url,
        'element_type': genomicElement.type,
        'element_chr': genomicElement.chr,
        'element_start': genomicElement.start,
        'element_end': genomicElement.end
      }
    )

    RETURN (gene != NULL ? { 'gene': gene, 'elements': elements }: {})
  `
  return (await (await db.query(query)).all())[0]
}

async function findGenesFromGenomicElementsSearch (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let customFilter = edgeQuery(input)
  if (customFilter !== '') {
    customFilter = `and ${customFilter}`
  }

  if (input.region === undefined) {
    throw new TRPCError({
      code: 'NOT_FOUND',
      message: 'Region must be defined.'
    })
  }

  const biosampleIDs = await getBiosampleIDs(input)

  const genomicElementsFilters = getFilterStatements(genomicElementSchema, preProcessRegionParam(input))

  const query = `
    LET sources = (
      FOR record in ${genomicElementSchema.db_collection_name as string} OPTIONS { indexHint: "${ZKD_INDEX}", forceIndexHint: true }
      FILTER ${genomicElementsFilters}
      RETURN record._id
    )

    FOR record IN ${genomicElementToGeneSchema.db_collection_name as string}
      FILTER record._from IN sources ${customFilter} ${biosampleIDs !== null ? `AND record.biological_context IN ['${biosampleIDs.join('\', \'')}']` : ''}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        ${getDBReturnStatements(genomicElementToGeneSchema)},
        'gene': ${input.verbose === 'true' ? `(${geneVerboseQuery})[0]` : 'record._to'},
        'genomic_elements': ${input.verbose === 'true' ? `(${genomicElementVerboseQuery})[0]` : 'record._from'},
        'biosample': ${input.verbose === 'true' ? 'DOCUMENT(record.biological_context)' : 'DOCUMENT(record.biological_context).name'},
      }
  `
  return await (await db.query(query)).all()
}

const genomicElementsQuery = genomicElementCommonQueryFormat.merge(z.object({
  region_type: z.enum([
    'accessible dna elements',
    'tested elements'
  ]).optional()
// eslint-disable-next-line @typescript-eslint/naming-convention
})).merge(commonBiosamplesQueryFormat).merge(edgeSources).merge(commonHumanEdgeParamsFormat).transform(({ region_type, ...rest }) => ({
  type: region_type,
  ...rest
}))

const genomicElementsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/genomic-elements', description: descriptions.genes_predictions } })
  .input(z.object({ gene_id: z.string() }).merge(commonNodesParamsFormat).omit({ organism: true }))
  .output(genomicElementFromGeneFormat)
  .query(async ({ input }) => await findGenomicElementsFromGene(input))

const genesFromGenomicElements = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genomic-elements/genes', description: descriptions.genomic_elements_genes } })
  .input(genomicElementsQuery)
  .output(z.array(genomicElementToGeneFormat))
  .query(async ({ input }) => await findGenesFromGenomicElementsSearch(input))

export const genomicElementsGenesRouters = {
  genomicElementsFromGenes,
  genesFromGenomicElements
}
