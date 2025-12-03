import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { variantIDSearch } from '../nodes/variants'
import { ontologyFormat } from '../nodes/ontologies'
import { getDBReturnStatements, paramsFormatType } from '../_helpers'
import { TRPCError } from '@trpc/server'
import { descriptions } from '../descriptions'
import { commonHumanEdgeParamsFormat, diseasessCommonQueryFormat, variantsCommonQueryFormat } from '../params'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 100

const assertionTypes = z.enum([
  'Benign',
  'Likely Benign',
  'Likely Pathogenic',
  'Pathogenic',
  'Uncertain Significance'
])

export const variantReturnFormat = z.object({
  chr: z.string(),
  pos: z.number(),
  ref: z.string(),
  alt: z.string(),
  rsid: z.array(z.string()).nullish(),
  spdi: z.string().optional(),
  hgvs: z.string().optional(),
  ca_id: z.string().nullish()
})

const variantDiseaseFormat = z.object({
  sequence_variant: z.string().or((variantReturnFormat)).optional(),
  disease: z.string().or(ontologyFormat).optional(),
  gene_id: z.string().optional(),
  gene_name: z.string().optional(),
  assertion: z.string().optional(),
  pmids: z.array(z.string()).optional(),
  source: z.string().optional(),
  source_url: z.string().optional(),
  name: z.string()
})

const variantDiseasQueryFormat = z.object({
  assertion: assertionTypes.optional(),
  pmid: z.string().trim().optional()
})

const variantSchema = getSchema('data/schemas/nodes/variants.Favor.json')
const variantCollectionName = variantSchema.db_collection_name as string
const diseaseSchema = getSchema('data/schemas/nodes/ontology_terms.Ontology.json')
const diseaseCollectionName = diseaseSchema.db_collection_name as string
const variantToDiseaseSchema = getSchema('data/schemas/edges/variants_diseases.ClinGen.json')
const variantToDiseaseCollectionName = variantToDiseaseSchema.db_collection_name as string

function validateInput (input: paramsFormatType): void {
  if (Object.keys(input).filter(item => !['limit', 'page', 'verbose', 'organism', 'pmid', 'assertion'].includes(item)).length === 0) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one node property for variant / disease must be defined.'
    })
  }
  if ((input.chr === undefined && input.position !== undefined) || (input.chr !== undefined && input.position === undefined)) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'Chromosome and position must be defined together.'
    })
  }
}

function edgeQuery (input: paramsFormatType): string {
  const query = []

  if (input.pmid !== undefined && input.pmid !== '') {
    const pmidUrl = 'http://pubmed.ncbi.nlm.nih.gov/'
    input.pmid = pmidUrl + (input.pmid as string)
    query.push(`'${input.pmid}' IN record.pmids`)
    delete input.pmid
  }

  if (input.assertion !== undefined) {
    query.push(`record.assertion == '${input.assertion as string}'`)
    delete input.assertion
  }

  return query.join(' and ')
}

const variantVerboseQuery = `
FOR otherRecord IN ${variantCollectionName}
FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
RETURN {${getDBReturnStatements(variantSchema).replaceAll('record', 'otherRecord')}}
`

const diseaseVerboseQuery = `
FOR otherRecord IN ${diseaseCollectionName}
FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
RETURN {${getDBReturnStatements(diseaseSchema).replaceAll('record', 'otherRecord')}}
`

async function DiseaseFromVariantSearch (input: paramsFormatType): Promise<any[]> {
  validateInput(input)
  // only allow human
  delete input.organism

  // eslint-disable-next-line @typescript-eslint/naming-convention
  const variantInput: paramsFormatType = (({ variant_id, spdi, hgvs, rsid, ca_id, chr, position }) => ({ variant_id, spdi, hgvs, rsid, ca_id, chr, position }))(input)
  delete input.variant_id
  delete input.spdi
  delete input.hgvs
  delete input.rsid
  delete input.chr
  delete input.position
  delete input.ca_id
  const variantIDs = await variantIDSearch(variantInput)

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

    FOR record IN ${variantToDiseaseCollectionName}
        FILTER record._from IN ['${variantIDs.join('\', \'')}'] ${edgeFilter}
        SORT record._key
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN {
            'sequence_variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
            'disease': ${verbose ? `(${diseaseVerboseQuery})[0]` : 'record._to'},
            'gene_name': DOCUMENT(record.gene_id)['name'],
            ${getDBReturnStatements(variantToDiseaseSchema)},
            'name': record.name
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
      FOR record IN ${variantToDiseaseCollectionName}
      FILTER record._to == 'ontology_terms/${input.disease_id as string}' ${edgeFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        'sequence_variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
        'disease': ${verbose ? `(${diseaseVerboseQuery})[0]` : 'record._to'},
        'gene_name': DOCUMENT(record.gene_id)['name'],
        ${getDBReturnStatements(variantToDiseaseSchema)},
        'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
    }
    `
  } else {
    if (input.disease_name !== undefined) {
      query = `
      LET diseaseIDs = (
        FOR record IN ontology_terms_text_en_no_stem_inverted_search_alias
        SEARCH TOKENS("${input.disease_name as string}", "text_en_no_stem") ALL in record.name
        SORT BM25(record) DESC
        RETURN record._id
        )

      FOR record IN ${variantToDiseaseCollectionName}
        FILTER record._to IN diseaseIDs ${edgeFilter}
        SORT record._key
        LIMIT ${input.page as number * limit}, ${limit}
        RETURN {
            'sequence_variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'},
            'disease': ${verbose ? `(${diseaseVerboseQuery})[0]` : 'record._to'},
            'gene_name': DOCUMENT(record.gene_id)['name'],
            ${getDBReturnStatements(variantToDiseaseSchema)},
            'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
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
  .input(diseasessCommonQueryFormat.merge(variantDiseasQueryFormat).merge(commonHumanEdgeParamsFormat))
  .output(z.array(variantDiseaseFormat))
  .query(async ({ input }) => await variantFromDiseaseSearch(input))

const diseaseFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/diseases', description: descriptions.variants_diseases } })
  .input(variantsCommonQueryFormat.merge(variantDiseasQueryFormat).merge(commonHumanEdgeParamsFormat))
  .output(z.array(variantDiseaseFormat))
  .query(async ({ input }) => await DiseaseFromVariantSearch(input))

export const variantsDiseasesRouters = {
  variantsFromDiseases,
  diseaseFromVariants
}
