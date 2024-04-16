import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { descriptions } from '../descriptions'

const MAX_PAGE_SIZE = 100

const schema = loadSchemaConfig()

const goTermsAnnotationsSchema = schema.gaf
const transcriptSchema = schema.transcript
const proteinSchema = schema.protein

const goTermQueryFormat = z.object({
  go_term_id: z.string(),
  page: z.number().default(0),
  limit: z.number().optional()
})

const queryFormat = z.object({
  query: z.string(),
  page: z.number().default(0),
  limit: z.number().optional()
})

const goAnnotationFormat = z.object({
  annotation_id: z.string(),
  annotation_name: z.string(),
  go_term_name: z.string(),
  source: z.string(),
  gene_product_type: z.string(),
  gene_product_symbol: z.string(),
  qualifier: z.array(z.string()),
  organism: z.string(),
  evidence: z.string(),
  go_id: z.string()
}).optional()

async function transcriptIds (id: string): Promise<any[]> {
  const input: paramsFormatType = {}
  input.transcript_name = id
  input.transcript_id = id
  input._key = id

  const query = `
    FOR record IN ${transcriptSchema.db_collection_name}
    FILTER ${getFilterStatements(transcriptSchema, input, 'or')}
    RETURN DISTINCT record._id
  `

  return await (await db.query(query)).all()
}

async function proteinIds (id: string): Promise<any[]> {
  const input: paramsFormatType = {}
  input.name = id
  input.dbxrefs = id
  input._key = id

  const query = `
    FOR record IN ${proteinSchema.db_collection_name}
    FILTER ${getFilterStatements(transcriptSchema, input, 'or')}
    RETURN DISTINCT record._id
  `

  return await (await db.query(query)).all()
}

const goTermAnnotationsCollection = goTermsAnnotationsSchema.db_collection_name

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

  if (annotations.length > 0) {
    const query = `
      FOR record IN ${goTermAnnotationsCollection}
        FILTER record._to IN ['${annotations.join('\',\'')}']
        LET sourceReturn = DOCUMENT(record._from)
        LET targetReturn = DOCUMENT(record._to)

        SORT record._from
        LIMIT ${page * limit}, ${limit}

        RETURN DISTINCT {
          'annotation_id': targetReturn._id,
          'annotation_name': targetReturn.name,
          'go_term_name': sourceReturn.name,
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

  const query = `
    FOR record IN ${goTermAnnotationsCollection}
      FILTER record._from == '${id}'
      LET sourceReturn = DOCUMENT(record._from)
      LET targetReturn = DOCUMENT(record._to)

      // if a protein is not found, the ID might be found in the DBXRefs.
      // for example: ENSEMBL:ENSMUSP00000113827
      LET dbxrefID = SPLIT(PARSE_IDENTIFIER(record._to).key, ':')[1] or 'invalid'
      LET dbxrefTargetReturn = (
        FOR dbxrefRecord IN proteins_fuzzy_search_alias
          SEARCH STARTS_WITH(dbxrefRecord['dbxrefs.id'], LOWER(dbxrefID))
          LIMIT 1
          SORT BM25(dbxrefRecord) DESC
          RETURN {'_id': dbxrefRecord._id, 'name': dbxrefRecord.name}
      )[0]

      SORT record._to
      LIMIT ${page * limit}, ${limit}

      RETURN DISTINCT {
        'annotation_id': targetReturn._id OR dbxrefTargetReturn._id,
        'annotation_name': targetReturn.name OR dbxrefTargetReturn.name,
        'go_term_name': sourceReturn.name,
        ${getDBReturnStatements(goTermsAnnotationsSchema)}
      }
  `

  return await (await db.query(query)).all()
}

const goTermsFromAnnotations = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/annotations/go-terms', description: descriptions.annotations_go_terms } })
  .input(queryFormat)
  .output(z.array(goAnnotationFormat))
  .query(async ({ input }) => await goTermsSearch(input))

const annotationsFromGoTerms = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/go-terms/annotations', description: descriptions.go_terms_annotations } })
  .input(goTermQueryFormat)
  .output(z.array(goAnnotationFormat))
  .query(async ({ input }) => await annotationsSearch(input))

export const goTermsAnnotations = {
  goTermsFromAnnotations,
  annotationsFromGoTerms
}
