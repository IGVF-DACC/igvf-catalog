import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { geneFormat, geneSearch } from '../nodes/genes'
import { ontologyFormat } from '../nodes/ontologies'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { TRPCError } from '@trpc/server'
import { descriptions } from '../descriptions'
import { commonHumanEdgeParamsFormat, diseasessCommonQueryFormat, genesCommonQueryFormat } from '../params'
import { getSchema } from '../schema'

const MAX_PAGE_SIZE = 100

const diseaseToGeneSchema = getSchema('data/schemas/edges/diseases_genes.Disease.json')
const diseaseToGeneCollectionName = diseaseToGeneSchema.db_collection_name as string
const diseaseSchema = getSchema('data/schemas/nodes/ontology_terms.Ontology.json')
const diseaseCollectionName = diseaseSchema.db_collection_name as string
const geneSchema = getSchema('data/schemas/nodes/genes.GencodeGene.json')
const geneCollectionName = geneSchema.db_collection_name as string
const variantToDiseaseToGeneSchema = getSchema('data/schemas/edges/variants_diseases_genes.ClinGen.json')
const variantToDiseaseToGeneCollectionName = variantToDiseaseToGeneSchema.db_collection_name as string
const variantToDiseaseCollectionName = 'variants_diseases'
const variantSchema = getSchema('data/schemas/nodes/variants.Favor.json')
const variantCollectionName = variantSchema.db_collection_name as string

const variantReturnFormat = z.object({
  chr: z.string(),
  pos: z.number(),
  ref: z.string(),
  alt: z.string(),
  rsid: z.array(z.string()).nullish(),
  spdi: z.string().optional(),
  hgvs: z.string().optional()
})

const diseasesToGenesFormat = z.object({
  pmid: z.array(z.string()).optional(),
  term_name: z.string().optional(),
  gene_symbol: z.string().optional(),
  association_type: z.string().optional(),
  association_status: z.string().optional(),
  source: z.string().optional(),
  source_url: z.string().optional(),
  gene: z.string().or(geneFormat).optional(),
  disease: z.string().or(ontologyFormat).optional(),
  inheritance_mode: z.string().optional(),
  variants: z.array(variantReturnFormat).optional(),
  name: z.string()
// eslint-disable-next-line @typescript-eslint/naming-convention
}).transform(({ association_type, ...rest }) => ({ Orphanet_association_type: association_type, ...rest }))
  // eslint-disable-next-line @typescript-eslint/naming-convention
  .transform(({ inheritance_mode, ...rest }) => ({ ClinGen_inheritance_mode: inheritance_mode, ...rest }))

const genesDiseasesQueryFormat = z.object({
  source: z.enum(['Orphanet', 'ClinGen']).optional()
})

const DiseasesGenesQueryFormat = z.object({
  source: z.enum(['Orphanet']).default('Orphanet')
})

// eslint-disable-next-line @typescript-eslint/naming-convention
const geneQuery = genesCommonQueryFormat.merge(genesDiseasesQueryFormat).merge(commonHumanEdgeParamsFormat).transform(({ gene_name, ...rest }) => ({
  name: gene_name,
  ...rest
}))

// eslint-disable-next-line @typescript-eslint/naming-convention
const diseaseQuery = diseasessCommonQueryFormat.merge(DiseasesGenesQueryFormat).merge(commonHumanEdgeParamsFormat).transform(({ disease_name, ...rest }) => ({
  term_name: disease_name,
  ...rest
}))

function validateGeneInput (input: paramsFormatType): void {
  const isInvalidFilter = Object.keys(input).every(item => !['gene_id', 'hgnc_id', 'name', 'alias'].includes(item) || input[item] === undefined)
  if (isInvalidFilter) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one gene property must be defined.'
    })
  }
}
function edgeQuery (input: paramsFormatType): string {
  const query = []

  if (input.source !== undefined && input.source !== '') {
    query.push(`record.source == '${input.source as string}'`)
    delete input.source
  }

  let strQuery = query.join('and ')
  if (strQuery !== '') {
    strQuery = `and ${strQuery}`
  }
  return strQuery
}

async function genesFromDiseaseSearch (input: paramsFormatType): Promise<any[]> {
  delete input.organism
  if (input.disease_id === undefined && input.term_name === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'disease_id or term_name must be defined.'
    })
  }
  if (input.Orphanet_association_type !== undefined) {
    input.association_type = input.Orphanet_association_type
    delete input.Orphanet_association_type
  }

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const verbose = input.verbose === 'true'

  if (input.disease_id !== undefined) {
    input._from = `ontology_terms/${input.disease_id as string}`
    delete input.disease_id

    const sourceQuery = `FOR otherRecord IN ${diseaseCollectionName}
      FILTER otherRecord._id == record._from
      RETURN {${getDBReturnStatements(diseaseSchema).replaceAll('record', 'otherRecord')}}
    `

    const targetQuery = `
      FOR otherRecord IN ${geneCollectionName}
      FILTER otherRecord._id == record._to
      RETURN {${getDBReturnStatements(geneSchema).replaceAll('record', 'otherRecord')}}
    `

    const sourceReturn = `'disease': ${verbose ? `(${sourceQuery})[0]` : 'record._from'},`
    const targetReturn = `'gene': ${verbose ? `(${targetQuery})[0]` : 'record._to'},`

    const query = `
      FOR record IN ${diseaseToGeneCollectionName}
      FILTER ${getFilterStatements(diseaseToGeneSchema, input)}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
      ${sourceReturn + targetReturn + getDBReturnStatements(diseaseToGeneSchema)},
      'name': record.name
      }
    `
    return await (await db.query(query)).all()
  }

  const searchTerm = input.term_name as string
  const searchViewName = `${diseaseToGeneCollectionName}_text_en_no_stem_inverted_search_alias`

  delete input.term_name

  const verboseQuery = `
    FOR otherRecord IN ${geneCollectionName}
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
        'gene': ${verbose ? `(${verboseQuery})[0]` : 'record._to'},
        'disease': ${verbose ? 'DOCUMENT(record._from)' : 'record._from'},
        'name': record.name
      }
  `
  return await (await db.query(query)).all()
}

async function diseasesFromGeneSearch (input: paramsFormatType): Promise<any[]> {
  validateGeneInput(input)
  // eslint-disable-next-line @typescript-eslint/naming-convention
  const { gene_id, hgnc_id, name, alias, organism } = input
  const geneInput: paramsFormatType = { gene_id, hgnc_id, name, alias, organism, page: 0 }
  delete input.hgnc_id
  delete input.gene_name
  delete input.alias
  delete input.organism

  const genes = await geneSearch(geneInput)
  const geneIDs = genes.map(gene => `genes/${gene._id as string}`)

  let limit = QUERY_LIMIT
  if (input.limit !== undefined) {
    limit = (input.limit as number <= MAX_PAGE_SIZE) ? input.limit as number : MAX_PAGE_SIZE
    delete input.limit
  }

  const verboseQueryORPHANET = `
    FOR otherRecord IN ${diseaseCollectionName}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(diseaseSchema).replaceAll('record', 'otherRecord')}}
  `

  const verboseQueryDiseaseClinGen = `
    FOR otherRecord IN ${diseaseCollectionName}
    FILTER otherRecord._key == PARSE_IDENTIFIER(edgeRecord._to).key
    RETURN {${getDBReturnStatements(diseaseSchema).replaceAll('record', 'otherRecord')}}
  `

  const verboseQueryVariantClinGen = `
    FOR otherRecord IN ${variantCollectionName}
    FILTER otherRecord._key == PARSE_IDENTIFIER(edgeRecord._from).key
    RETURN {${getDBReturnStatements(variantSchema, true).replaceAll('record', 'otherRecord')}}
  `
  const orphanetQuery = `
     LET ORPHANET = (
      FOR record IN ${diseaseToGeneCollectionName}
      FILTER record._to IN ${JSON.stringify(geneIDs)} ${edgeQuery(input)}
      SORT record._key
      RETURN {
        'disease': ${input.verbose === 'true' ? `(${verboseQueryORPHANET})[0]` : 'record._from'},
        ${getDBReturnStatements(diseaseToGeneSchema)},
        'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
      }
    )
  `

  const clinGenQuery = `
  LET CLINGEN = (
    FOR record IN ${variantToDiseaseToGeneCollectionName}
      FILTER record._to IN ${JSON.stringify(geneIDs)} ${edgeQuery(input)}
      SORT record._key
      RETURN (
        FOR edgeRecord IN ${variantToDiseaseCollectionName}
        FILTER edgeRecord._key == PARSE_IDENTIFIER(record._from).key
        RETURN {
          'disease': edgeRecord._to,
          'term_name': DOCUMENT(edgeRecord._to)['name'],
          ${getDBReturnStatements(variantToDiseaseToGeneSchema)},
          'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
        }
      )[0]
    )

  LET CLINGENUNIQ = (
    FOR record IN CLINGEN
    RETURN DISTINCT record

  )
  `

  const clinGenVerboseQuery = `
  LET CLINGEN = (
    FOR record IN ${variantToDiseaseToGeneCollectionName}
      FILTER record._to IN ${JSON.stringify(geneIDs)} ${edgeQuery(input)}
      SORT record._key
      RETURN (
        FOR edgeRecord IN ${variantToDiseaseCollectionName}
        FILTER edgeRecord._key == PARSE_IDENTIFIER(record._from).key
        RETURN {
          'variant': ${`(${verboseQueryVariantClinGen})[0]`},
          'disease': ${`(${verboseQueryDiseaseClinGen})[0]`},
          ${getDBReturnStatements(variantToDiseaseToGeneSchema)},
          'name': record.inverse_name // endpoint is opposite to ArangoDB collection name
        }
      )[0]
    )

  LET CLINGENUNIQ = (
    FOR record IN CLINGEN
    COLLECT disease = record.disease, inheritance_mode = record.inheritance_mode, source = record.source, source_url = record.source_url, name = record.name INTO variantGroup = record.variant
    LET variants = (
      FOR v IN variantGroup
        FILTER v != null
        RETURN v
    )
    RETURN {
      'variants': variants,
      'disease': disease,
      'inheritance_mode': inheritance_mode,
      'source': source,
      'source_url': source_url,
      'name': name
    }
  )

  `
  const query = `
    ${orphanetQuery}
    ${input.verbose === 'true' ? clinGenVerboseQuery : clinGenQuery}

    FOR record in UNION(ORPHANET, CLINGENUNIQ)
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN record
  `

  return await (await db.query(query)).all()
}

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
