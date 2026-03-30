import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'
import { commonNodesParamsFormat } from '../params'
import { getSchema, getCollectionEnumValuesOrThrow } from '../schema'

const MAX_PAGE_SIZE = 100

const goTermsAnnotationsSchema = getSchema('data/schemas/edges/gene_products_terms.GAF.json')
const transcriptSchema = getSchema('data/schemas/nodes/transcripts.Gencode.json')
const transcriptCollectionName = transcriptSchema.db_collection_name as string
const proteinSchema = getSchema('data/schemas/nodes/proteins.GencodeProtein.json')
const proteinCollectionName = proteinSchema.db_collection_name as string
const geneProductsTermsName = getCollectionEnumValuesOrThrow('edges', 'gene_products_terms', 'name')
const geneProductsTermsInverseName = getCollectionEnumValuesOrThrow('edges', 'gene_products_terms', 'inverse_name')

const goTermQueryFormat = z.object({
  go_term_id: z.string(),
  name: z.enum(geneProductsTermsInverseName).optional()
}).merge(commonNodesParamsFormat).omit({ organism: true })

const queryFormat = z.object({
  query: z.string(),
  name: z.enum(geneProductsTermsName).optional(),
  page: z.number().default(0),
  limit: z.number().optional()
})

const goAnnotationFormat = z.object({
  gene_product_id: z.string(),
  gene_product_name: z.string().nullish(),
  go_term_name: z.string(),
  source: z.string(),
  gene_product_type: z.string(),
  gene_product_symbol: z.string(),
  qualifier: z.array(z.string()),
  organism: z.string(),
  evidence: z.string(),
  go_id: z.string(),
  name: z.string()
}).optional()

async function transcriptIds (id: string): Promise<any[]> {
  const input: paramsFormatType = {}
  input.name = id
  input.transcript_id = id
  input._key = id

  const query = `
    FOR record IN ${transcriptCollectionName}
    FILTER ${getFilterStatements(transcriptSchema, input, 'or')}
    RETURN DISTINCT record._id
  `

  return await (await db.query(query)).all()
}

async function proteinIds (id: string): Promise<any[]> {
  const input: paramsFormatType = {}
  input.name = id
  input.dbxrefs = id
  input.uniprot_names = id
  input._key = id

  const query = `
    FOR record IN ${proteinCollectionName}
    FILTER ${getFilterStatements(proteinSchema, input, 'or')}
    RETURN DISTINCT record._id
  `
  return await (await db.query(query)).all()
}

const goTermAnnotationsCollection = goTermsAnnotationsSchema.db_collection_name as string

async function goTermsSearch (input: paramsFormatType): Promise<any[]> {
  const query = input.query as string
  const page = input.page as number

  let annotations: string[]

  // assuming an ID will match either transcripts or proteins
  const transcripts = await transcriptIds(query)
  if (transcripts.length !== 0) {
    annotations = transcripts
  } else {
    annotations = await proteinIds(query)
  }
  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filters = ''
  if (input.name !== undefined) {
    filters += ` AND record.name == '${input.name as string}'`
  }

  if (annotations.length > 0) {
    const query = `
      FOR record IN ${goTermAnnotationsCollection}
        FILTER record._from IN ['${annotations.join('\',\'')}'] ${filters}
        LET sourceReturn = DOCUMENT(record._from)
        LET targetReturn = DOCUMENT(record._to)

        SORT record._to
        LIMIT ${page * limit}, ${limit}

        RETURN DISTINCT {
          'name': record.name,
          'gene_product_id': sourceReturn._id,
          'gene_product_name': sourceReturn.name,
          'go_term_name': targetReturn.name,
          ${getDBReturnStatements(goTermsAnnotationsSchema)}
        }
    `
    return await (await db.query(query)).all()
  }

  return []
}

async function annotationsSearch (input: paramsFormatType): Promise<any[]> {
  const id = `ontology_terms/${input.go_term_id as string}`
  const page = input.page as number

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  let filters = ''
  if (input.name !== undefined) {
    filters += ` AND record.inverse_name == '${input.name as string}'`
  }

  const query = `
    FOR record IN ${goTermAnnotationsCollection}
      FILTER record._to == '${id}' ${filters}
      LET sourceReturn = DOCUMENT(record._from)
      LET targetReturn = DOCUMENT(record._to)

      // if a protein is not found, the ID might be found in the DBXRefs.
      // for example: ENSEMBL:ENSMUSP00000113827
      LET dbxrefID = SPLIT(PARSE_IDENTIFIER(record._to).key, ':')[1] or 'invalid'
      LET dbxrefTargetReturn = (
        FOR dbxrefRecord IN proteins_text_en_no_stem_inverted_search_alias
          SEARCH STARTS_WITH(dbxrefRecord['dbxrefs.id'], LOWER(dbxrefID))
          LIMIT 1
          SORT BM25(dbxrefRecord) DESC
          RETURN {'_id': dbxrefRecord._id, 'name': dbxrefRecord.name}
      )[0]

      SORT record._from
      LIMIT ${page * limit}, ${limit}

      RETURN DISTINCT {
        'name': record.inverse_name,
        'gene_product_id': sourceReturn._id OR dbxrefTargetReturn._id,
        'gene_product_name': sourceReturn.name
        'go_term_name': targetReturn.name,
        ${getDBReturnStatements(goTermsAnnotationsSchema)}
      }
  `
  return await (await db.query(query)).all()
}

const goTermsFromAnnotations = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/gene-products/go-terms', description: descriptions.annotations_go_terms } })
  .input(queryFormat)
  .output(z.array(goAnnotationFormat))
  .query(async ({ input }) => await goTermsSearch(input))

const annotationsFromGoTerms = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/go-terms/gene-products', description: descriptions.go_terms_annotations } })
  .input(goTermQueryFormat)
  .output(z.array(goAnnotationFormat))
  .query(async ({ input }) => await annotationsSearch(input))

export const goTermsAnnotations = {
  goTermsFromAnnotations,
  annotationsFromGoTerms
}
