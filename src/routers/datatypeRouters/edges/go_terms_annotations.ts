import { z } from 'zod'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { RouterEdges } from '../../genericRouters/routerEdges'
import { paramsFormatType } from '../_helpers'
import { RouterFilterBy } from '../../genericRouters/routerFilterBy'
import { descriptions } from '../descriptions'

const schema = loadSchemaConfig()

const transcriptSchema = schema.transcript
const proteinSchema = schema.protein

const goTermsAnnotationsSchema = schema.gaf
const goAnnotationsRouter = new RouterEdges(goTermsAnnotationsSchema)

const goTermQueryFormat = z.object({
  go_term_id: z.string(),
  page: z.number().default(0)
})

const queryFormat = z.object({
  query: z.string(),
  page: z.number().default(0)
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

  return await (new RouterFilterBy(transcriptSchema)).getObjectIDs(input, '', false)
}

async function proteinIds (id: string): Promise<any[]> {
  const input: paramsFormatType = {}
  input.name = id
  input.dbxrefs = id
  input._key = id

  return await (new RouterFilterBy(proteinSchema)).getObjectIDs(input, '', false)
}

const customSourceFields = "'go_term_name': record.term_name"
const customTargetFields = "'annotation_id': record._id, 'annotation_name': record['name'] OR record['transcript_name']"

async function goTermsSearch (input: paramsFormatType): Promise<any[]> {
  const query = input.query as string
  const page = input.page as number

  let response

  let annotations: string[]

  // assuming an ID will match either a transcript or a protein
  const transcripts = await transcriptIds(query)
  if (transcripts.length !== 0) {
    annotations = transcripts
  } else {
    annotations = await proteinIds(query)
  }

  if (annotations.length > 0) {
    response = await goAnnotationsRouter.getSourceAndEdgeSet(annotations, customSourceFields, customTargetFields, 'transcripts', page)

    return response
  }

  return []
}

async function annotationsSearch (input: paramsFormatType): Promise<any[]> {
  const id = `ontology_terms/${input.go_term_id as string}`
  const page = input.page as number

  return await goAnnotationsRouter.getTargetAndEdgeSet(id, customSourceFields, customTargetFields, page)
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
