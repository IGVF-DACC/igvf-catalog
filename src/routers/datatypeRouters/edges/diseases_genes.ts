import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { geneFormat, genesQueryFormat } from '../nodes/genes'
import { ontologyFormat } from '../nodes/ontologies'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { TRPCError } from '@trpc/server'
import { descriptions } from '../descriptions'

const MAX_PAGE_SIZE = 100

const associationTypes = z.object({
  association_type: z.enum([
    'Disease-causing germline mutation(s) in',
    'Modifying germline mutation in',
    'Major susceptibility factor in',
    'Candidate gene tested in',
    'Disease-causing germline mutation(s) (loss of function) in',
    'Disease-causing somatic mutation(s) in',
    'Disease-causing germline mutation(s) (gain of function) in',
    'Role in the phenotype of',
    'Part of a fusion gene in',
    'Biomarker tested in'
  ]).optional()
})

const schema = loadSchemaConfig()
const diseaseToGeneSchema = schema['disease to gene']
const diseaseSchema = schema['ontology term']
const geneSchema = schema.gene

const diseasesToGenesFormat = z.object({
  pmid: z.array(z.string()).optional(),
  term_name: z.string().optional(),
  gene_symbol: z.string().optional(),
  association_type: z.string().optional(),
  association_status: z.string().optional(),
  source: z.string().optional(),
  source_url: z.string().optional(),
  gene: z.string().or(geneFormat).optional(),
  'disease': z.string().or(ontologyFormat).optional()
})

function edgeQuery (input: paramsFormatType): string {
  const query = []

  if (input.association_type !== undefined && input.association_type !== '') {
    query.push(`record.association_type == '${input.association_type}'`)
    delete input.association_type
  }

  if (input.source !== undefined && input.source !== '') {
    query.push(`record.source == '${input.source}'`)
    delete input.source
  }

  if (Object.keys(input).filter(item => !['page', 'verbose'].includes(item)).length === 0) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one gene property must be defined.'
    })
  }

  return query.join('and ')
}

async function genesFromDiseaseSearch (input: paramsFormatType): Promise<any[]> {
  if (Object.keys(input).filter(item => !['disease_id', 'term_name'].includes(item)).length === 0) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one gene property must be defined.'
    })
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const verbose = input.verbose === 'true'

  if (input.disease_id !== undefined) {
    input._from = `ontology_terms/${input.disease_id}`
    delete input.disease_id

    const sourceQuery = `FOR otherRecord IN ${diseaseSchema.db_collection_name}
      FILTER otherRecord._id == record._from
      RETURN {${getDBReturnStatements(diseaseSchema).replaceAll('record', 'otherRecord')}}
    `

    const targetQuery = `
      FOR otherRecord IN ${geneSchema.db_collection_name}
      FILTER otherRecord._id == record._to
      RETURN {${getDBReturnStatements(geneSchema).replaceAll('record', 'otherRecord')}}
    `

    const sourceReturn = `'disease': ${verbose ? `(${sourceQuery})[0]` : 'record._from'},`
    const targetReturn = `'gene': ${verbose ? `(${targetQuery})[0]` : 'record._to'},`

    const query = `
      FOR record IN ${diseaseToGeneSchema.db_collection_name}
      FILTER ${getFilterStatements(diseaseToGeneSchema, input)}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN { ${sourceReturn + targetReturn + getDBReturnStatements(diseaseToGeneSchema)} }
    `

    return await (await db.query(query)).all()
  }

  const searchTerm = input.term_name as string
  const searchViewName = `${diseaseToGeneSchema.db_collection_name}_fuzzy_search_alias`

  delete input.term_name

  const verboseQuery = `
    FOR otherRecord IN ${geneSchema.db_collection_name}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(geneSchema).replaceAll('record', 'otherRecord')}}
  `

  let filters = getFilterStatements(diseaseToGeneSchema, input)
  if (filters !== '') {
    filters = `FILTER ${filters}`
  }

  const query = `
    FOR record IN ${searchViewName}
      SEARCH TOKENS("${decodeURIComponent(searchTerm)}", "text_en_no_stem") ALL in record.term_name
      SORT BM25(record) DESC
      ${filters}
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        ${getDBReturnStatements(diseaseToGeneSchema)},
        'gene': ${verbose ? `(${verboseQuery})[0]` : 'record._to'}
      }
  `

  return await (await db.query(query)).all()
}

async function diseasesFromGeneSearch (input: paramsFormatType): Promise<any[]> {
  if (input.gene_id !== undefined) {
    input._id = `genes/${input.gene_id}`
    delete input.gene_id
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let customFilter = edgeQuery(input)
  if (customFilter !== '') {
    customFilter = `and ${customFilter}`
  }

  const verboseQuery = `
    FOR otherRecord IN ${diseaseSchema.db_collection_name}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(diseaseSchema).replaceAll('record', 'otherRecord')}}
  `

  const query = `
    LET targets = (
      FOR record IN ${geneSchema.db_collection_name}
      FILTER ${getFilterStatements(geneSchema, preProcessRegionParam(input))}
      RETURN record._id
    )

    FOR record IN ${diseaseToGeneSchema.db_collection_name}
      FILTER record._to IN targets ${customFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'disease': ${input.verbose === 'true' ? `(${verboseQuery})[0]` : 'record._from'},
        ${getDBReturnStatements(diseaseToGeneSchema)}
      }
  `

  return await (await db.query(query)).all()
}

const geneQuery = genesQueryFormat.omit({
  organism: true,
  name: true
}).merge(z.object({
  gene_name: z.string().trim().optional(),
  source: z.string().trim().optional(),
  page: z.number().default(0),
  verbose: z.enum(['true', 'false']).default('false'),
  limit: z.number().optional()
})).merge(associationTypes).transform(({gene_name, ...rest}) => ({
  name: gene_name,
  ...rest
}))

const diseaseQuery = associationTypes.merge(z.object({
  disease_id: z.string().trim().optional(),
  term_name: z.string().trim().optional(),
  source: z.string().trim().optional(),
  page: z.number().default(0),
  verbose: z.enum(['true', 'false']).default('false'),
  limit: z.number().optional()
}))

const diseasesFromGenes = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/genes/diseases', description: descriptions.genes_diseases } })
  .input(geneQuery)
  .output(z.array(diseasesToGenesFormat))
  .query(async ({ input }) => await diseasesFromGeneSearch(input))

const genesFromDiseases = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/diseases/genes', description: descriptions.diseases_genes } })
  .input(diseaseQuery)
  .output(z.array(diseasesToGenesFormat))
  .query(async ({ input }) => await genesFromDiseaseSearch(input))

export const diseasesGenesRouters = {
  genesFromDiseases,
  diseasesFromGenes
}
