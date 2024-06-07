import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { variantsQueryFormat } from '../nodes/variants'
import { ontologyFormat } from '../nodes/ontologies'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { TRPCError } from '@trpc/server'
import { descriptions } from '../descriptions'

const MAX_PAGE_SIZE = 100

const assertionTypes = z.enum([
  'Benign',
  'Likely Benign',
  'Likely Pathogenic',
  'Pathogenic',
  'Uncertain Significance'
])

const variantReturnFormat = z.object({
  chr: z.string(),
  pos: z.number(),
  ref: z.string(),
  alt: z.string(),
  rsid: z.array(z.string()).nullish(),
  spdi: z.string().optional(),
  hgvs: z.string().optional()
})

const variantDiseaseFormat = z.object({
  'sequence variant': z.string().or((variantReturnFormat)).optional(),
  disease: z.string().or(ontologyFormat).optional(),
  gene_id: z.string().optional(),
  gene_name: z.string().optional(),
  assertion: z.string().optional(),
  pmids: z.array(z.string()).optional(),
  source: z.string().optional(),
  source_url: z.string().optional()
})

const variantDiseasQueryFormat = z.object({
  organism: z.enum(['Homo sapiens']),
  assertion: assertionTypes.optional(),
  pmid: z.string().trim().optional(),
  verbose: z.enum(['true', 'false']).default('false'),
  limit: z.number().optional()
})

const diseaseQueryFormat = z.object({
  disease_id: z.string().trim().optional(),
  disease_name: z.string().trim().optional(),
  page: z.number().default(0)
})

const schema = loadSchemaConfig()

const variantSchema = schema['sequence variant']
const diseaseSchema = schema['ontology term']
const variantToDiseaseSchema = schema['variant to disease']

function edgeQuery (input: paramsFormatType): string {
  const query = []

  if (input.pmid !== undefined && input.pmid !== '') {
    const pmidUrl = 'http://pubmed.ncbi.nlm.nih.gov/'
    input.pmid = pmidUrl + (input.pmid as string)
    query.push(`'${input.pmid}' IN record.pmids`)
    delete input.pmid
  }

  if (input.assertion !== undefined) {
    query.push(`record.assertion == '${input.assertion}'`)
    delete input.assertion
  }

  return query.join(' and ')
}

const variantVerboseQuery = `
FOR otherRecord IN ${variantSchema.db_collection_name as string}
FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
RETURN {${getDBReturnStatements(variantSchema).replaceAll('record', 'otherRecord')}}
`

const diseaseVerboseQuery = `
FOR otherRecord IN ${diseaseSchema.db_collection_name as string}
FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
RETURN {${getDBReturnStatements(diseaseSchema).replaceAll('record', 'otherRecord')}}
`

async function DiseaseFromVariantSearch (input: paramsFormatType): Promise<any[]> {
  // only allow human
  delete input.organism

  if (input.variant_id !== undefined) {
    input._id = `variants/${input.variant_id}`
    delete input.variant_id
  }

  const verbose = input.verbose === 'true'
  delete input.verbose

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let edgeFilter = edgeQuery(input)
  if (edgeFilter !== '') {
    edgeFilter = `and ${edgeFilter}`
  }

  const query = `
    LET variantIDs = (
        FOR record in ${variantSchema.db_collection_name as string}
        FILTER ${getFilterStatements(variantSchema, input)}
        RETURN record._id
    )

    FOR record IN ${variantToDiseaseSchema.db_collection_name as string}
        FILTER record._from IN variantIDs ${edgeFilter}
        SORT record._key
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN {
            'sequence variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
            'disease': ${verbose ? `(${diseaseVerboseQuery})[0]` : 'record._to'},
            'gene_name': DOCUMENT(record.gene_id)['name'],
            ${getDBReturnStatements(variantToDiseaseSchema)}
        }
  `

  return await (await db.query(query)).all()
}

async function variantFromDiseaseSearch (input: paramsFormatType): Promise<any[]> {
  // only allow human
  delete input.organism

  const verbose = input.verbose === 'true'
  delete input.verbose

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let edgeFilter = edgeQuery(input)
  if (edgeFilter !== '') {
    edgeFilter = `and ${edgeFilter}`
  }

  let query = ''

  if (input.disease_id !== undefined) {
    query = `
      FOR record IN ${variantToDiseaseSchema.db_collection_name as string}
      FILTER record._to == 'ontology_terms/${input.disease_id}' ${edgeFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'sequence variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
        'disease': ${verbose ? `(${diseaseVerboseQuery})[0]` : 'record._to'},
        'gene_name': DOCUMENT(record.gene_id)['name'],
        ${getDBReturnStatements(variantToDiseaseSchema)}
    }
    `
  } else {
    if (input.disease_name !== undefined) {
      query = `
      LET diseaseIDs = (
        FOR record IN ontology_terms_fuzzy_search_alias
        SEARCH TOKENS("${input.disease_name}", "text_en_no_stem") ALL in record.name
        SORT BM25(record) DESC
        RETURN record._id
        )

      FOR record IN ${variantToDiseaseSchema.db_collection_name as string}
        FILTER record._to IN diseaseIDs ${edgeFilter}
        SORT record._key
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN {
            'sequence variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
            'disease': ${verbose ? `(${diseaseVerboseQuery})[0]` : 'record._to'},
            'gene_name': DOCUMENT(record.gene_id)['name'],
            ${getDBReturnStatements(variantToDiseaseSchema)}
        }
    `
    } else {
      throw new TRPCError({
        code: 'BAD_REQUEST',
        message: 'disease_id or term_name must be defined.'
      })
    }
  }

  return await (await db.query(query)).all()
}

const variantsFromDiseases = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/diseases/variants', description: descriptions.diseases_variants } })
  .input(diseaseQueryFormat.merge(variantDiseasQueryFormat))
  .output(z.array(variantDiseaseFormat))
  .query(async ({ input }) => await variantFromDiseaseSearch(input))

const diseaseFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/diseases', description: descriptions.variants_diseases } })
  .input(variantsQueryFormat.omit({ mouse_strain: true, region: true, funseq_description: true, organism: true }).merge(variantDiseasQueryFormat))
  .output(z.array(variantDiseaseFormat))
  .query(async ({ input }) => await DiseaseFromVariantSearch(input))

export const variantsDiseasesRouters = {
  variantsFromDiseases,
  diseaseFromVariants
}
