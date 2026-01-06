import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { geneFormat, geneSearch } from '../nodes/genes'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { genomicElementFormat } from '../nodes/genomic_elements'
import { descriptions } from '../descriptions'
import { TRPCError } from '@trpc/server'
import { commonBiosamplesQueryFormat, commonHumanEdgeParamsFormat, commonNodesParamsFormat, genomicElementCommonQueryFormat } from '../params'
import { ontologyFormat } from '../nodes/ontologies'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 500
const METHODS = [
  'CRISPR enhancer perturbation screens',
  'CRISPR FACS screen',
  'ENCODE-rE2G',
  'Perturb-seq'
] as const

const genomicElementToGeneSchema = getSchema('data/schemas/edges/genomic_elements_genes.ENCODE2GCRISPR.json')
const genomicElementToGeneCollectionName = genomicElementToGeneSchema.db_collection_name as string
const genomicElementSchema = getSchema('data/schemas/nodes/genomic_elements.CCRE.json')
const genomicElementCollectionName = genomicElementSchema.db_collection_name as string
const geneSchema = getSchema('data/schemas/nodes/genes.GencodeGene.json')
const geneCollectionName = geneSchema.db_collection_name as string

const edgeSources = z.object({
  source: z.enum([
    'ENCODE',
    'IGVF'
  ]).optional()
})

const genesGenomicElementsInputFormat = genesCommonQueryFormat.merge(z.object({
  gene_id: z.string().optional(),
  method: z.enum(METHODS).optional(),
  files_fileset: z.string().optional()
}).merge(commonNodesParamsFormat).omit({ organism: true }))

const genomicElementToGeneFormat = z.object({
  score: z.number().nullable(),
  source: z.string().optional(),
  source_url: z.string().optional(),
  significant: z.boolean().nullish(),
  genomic_element: z.string().or(genomicElementFormat).optional(),
  gene: z.string().or(geneFormat).optional(),
  biosample: z.string().or(ontologyFormat).nullable(),
  name: z.string(),
  method: z.string().optional(),
  class: z.string().optional(),
  files_filesets: z.string().nullish()
})

const elementOutputFormat = z.object({
  id: z.string(),
  cell_type: z.string().nullish(),
  score: z.number().nullish(),
  model: z.string().nullish(),
  dataset: z.string().nullish(),
  element_type: z.string().nullish(),
  element_chr: z.string().nullish(),
  element_start: z.number().nullish(),
  element_end: z.number().nullish(),
  name: z.string(),
  method: z.string().optional(),
  class: z.string().optional(),
  files_filesets: z.string().nullish()
})

const geneOutputFormat = z.object({
  name: z.string(),
  _id: z.string(),
  start: z.number(),
  end: z.number(),
  chr: z.string()
})

const genesGenomicElementsOutputFormat = z.array(z.object({
  gene: geneOutputFormat,
  elements: z.array(elementOutputFormat).or(elementOutputFormat)
}))

function edgeQuery (input: paramsFormatType): string {
  let query = ''

  if (input.source !== undefined) {
    query = `record.source == '${input.source as string}'`
    delete input.source
  }

  return query
}

const geneVerboseQuery = `
    FOR otherRecord IN ${geneCollectionName}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(geneSchema).replaceAll('record', 'otherRecord')}}
  `

const genomicElementVerboseQuery = `
  FOR otherRecord IN ${genomicElementCollectionName}
  FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
  RETURN {${getDBReturnStatements(genomicElementSchema).replaceAll('record', 'otherRecord')}}
`

async function findGenomicElementsFromGene (input: paramsFormatType): Promise<any> {
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = ` AND record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
  }

  let methodFilter = ''
  if (input.method !== undefined) {
    methodFilter = ` AND record.method == '${input.method as string}'`
    delete input.method
  }

  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { gene_id, hgnc_id, gene_name: name, alias, organism } = input
  const geneInput: paramsFormatType = { gene_id, hgnc_id, name, alias, organism, page: 0 }
  delete input.gene_id
  delete input.hgnc_id
  delete input.alias
  delete input.gene_name
  delete input.organism
  const empty = Object.entries(geneInput).filter(([k]) => k !== 'page').every(([, v]) => v === undefined)

  let geneIDs: string[] = []
  if (!empty) {
    const genes = await geneSearch(geneInput)
    geneIDs = genes.map(gene => `${geneCollectionName}/${gene._id as string}`)

    if (geneIDs.length === 0) {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: 'Gene not found.'
      })
    }
  } else {
    if (filesetFilter !== '') {
      filesetFilter = filesetFilter.replace('AND', '')
    }

    if (methodFilter !== '' && filesetFilter === '') {
      methodFilter = methodFilter.replace('AND', '')
    }

    if (filesetFilter === '' && methodFilter === '') {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: 'At least one parameter must be defined.'
      })
    }
  }

  const query = `
    FOR record IN genomic_elements_genes
    FILTER ${empty ? '' : `record._to IN ['${geneIDs.join('\', \'')}']`} ${filesetFilter} ${methodFilter}
    SORT record._key
    LIMIT ${input.page as number * limit}, ${limit}

    LET genomicElement = DOCUMENT(record._from)

    COLLECT gene = DOCUMENT(record._to) INTO rows = {
      id: record._from,
      cell_type: record.biological_context,
      score: record.score,
      model: record.source,
      files_filesets: record.files_filesets,
      dataset: record.source_url,
      element_type: genomicElement.type,
      element_chr: genomicElement.chr,
      element_start: genomicElement.start,
      element_end: genomicElement.end,
      name: record.inverse_name,
      class: record.class,
      method: record.method
    }

    RETURN {
      gene,
      elements: rows
    }
  `

  return (await (await db.query(query)).all())
}

async function findGenesFromGenomicElementsSearch (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filesetFilter = ''
  if (input.files_fileset !== undefined) {
    filesetFilter = ` AND record.files_filesets == 'files_filesets/${input.files_fileset as string}'`
    delete input.files_fileset
  }

  let methodFilter = ''
  if (input.method !== undefined) {
    methodFilter = ` AND record.method == '${input.method as string}'`
    delete input.method
  }

  let customFilter = edgeQuery(input)
  if (customFilter !== '') {
    customFilter = `and ${customFilter}`
  }

  const genomicElementsFilters = getFilterStatements(genomicElementSchema, preProcessRegionParam(input))
  let biosampleIDs
  const empty = genomicElementsFilters === ''
  if (empty) {
    if (filesetFilter !== '') {
      filesetFilter = filesetFilter.replace('AND', '')
    }

    if (methodFilter !== '' && filesetFilter === '') {
      methodFilter = methodFilter.replace('AND', '')
    }

    if (filesetFilter === '' && methodFilter === '') {
      throw new TRPCError({
        code: 'NOT_FOUND',
        message: 'Region or files_fileset must be defined.'
      })
    }
  }

  let biosampleFilter = ''
  if (input.biosample_name !== undefined) {
    biosampleFilter = ` AND record.biological_context == '${input.biosample_name as string}'`
  }

  const query = `
  ${empty
    ? ''
    : `
      LET sources = (
        FOR record in ${genomicElementCollectionName}
        FILTER ${genomicElementsFilters}
        RETURN record._id
      )`
  }

    FOR record IN ${genomicElementToGeneCollectionName}
      FILTER ${empty ? '' : `record._from IN sources ${customFilter} ${biosampleFilter}`} ${filesetFilter} ${methodFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'name': record.name,
        'method': record.method,
        'class': record.class,
        'files_filesets': record.files_filesets,
        ${getDBReturnStatements(genomicElementToGeneSchema)},
        'gene': ${input.verbose === 'true' ? `(${geneVerboseQuery})[0]` : 'record._to'},
        'genomic_element': ${input.verbose === 'true' ? `(${genomicElementVerboseQuery})[0]` : 'record._from'},
        'biosample': record.biological_context
      }
  `

  return await (await db.query(query)).all()
}

const genomicElementsQuery = genomicElementCommonQueryFormat
  .merge(z.object({
    method: z.enum(METHODS).optional(),
    files_fileset: z.string().optional()
  }))
  .merge(commonBiosamplesQueryFormat)
  .merge(edgeSources)
  .merge(commonHumanEdgeParamsFormat)
  // eslint-disable-next-line @typescript-eslint/naming-convention
  .transform(({ region_type, ...rest }) => ({
    type: region_type,
    ...rest
  }))

const genomicElementsFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/genomic-elements', description: descriptions.genes_predictions } })
  .input(genesGenomicElementsInputFormat)
  .output(genesGenomicElementsOutputFormat)
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
