import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { geneFormat } from '../nodes/genes'
import { ontologyFormat } from '../nodes/ontologies'
import { getDBReturnStatements, getFilterStatements, paramsFormatType, preProcessRegionParam } from '../_helpers'
import { TRPCError } from '@trpc/server'
import { descriptions } from '../descriptions'
import { commonHumanEdgeParamsFormat, diseasessCommonQueryFormat, genesCommonQueryFormat } from '../params'

const MAX_PAGE_SIZE = 100

const schema = loadSchemaConfig()
const diseaseToGeneSchema = schema['disease to gene']
const diseaseSchema = schema['ontology term']
const geneSchema = schema.gene
const variantToDiseaseToGeneSchema = schema['variant to disease to gene']
const variantToDiseaseSchema = schema['variant to disease']
const variantSchema = schema['sequence variant']

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
  variants: z.array(variantReturnFormat).optional()
}).transform(({ association_type, ...rest }) => ({ Orphanet_association_type: association_type, ...rest }))
  .transform(({ inheritance_mode, ...rest }) => ({ ClinGen_inheritance_mode: inheritance_mode, ...rest }))

const genesDiseasesQueryFormat = z.object({
  source: z.enum(['Orphanet', 'ClinGen']).optional(),
  Orphanet_association_type: z.enum([
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
  ]).optional(),
  ClinGen_inheritance_mode: z.enum([
    'Autosomal dominant inheritance',
    'Autosomal dominant inheritance (mosaic)',
    'Autosomal dominant inheritance (with paternal imprinting (HP:0012274))',
    'Autosomal recessive inheritance',
    'Autosomal recessive inheritance (with genetic anticipation)',
    'Semidominant inheritance',
    'X-linked inheritance',
    'X-linked inheritance (dominant (HP:0001423))'
  ]).optional()
})
const geneQuery = genesCommonQueryFormat.merge(genesDiseasesQueryFormat).merge(commonHumanEdgeParamsFormat).transform(({gene_name, ...rest}) => ({
  name: gene_name,
  ...rest
}))

const diseaseQuery = diseasessCommonQueryFormat.merge(genesDiseasesQueryFormat).merge(commonHumanEdgeParamsFormat).omit({ ClinGen_inheritance_mode: true }).transform(({disease_name, ...rest}) => ({
  term_name: disease_name,
  ...rest
}))
function edgeQuery (input: paramsFormatType): string {
  const query = []

  if (input.Orphanet_association_type !== undefined && input.Orphanet_association_type !== '') {
    query.push(`record.association_type == '${input.Orphanet_association_type}'`)
    delete input.Orphanet_association_type
  }

  if (input.ClinGen_inheritance_mode !== undefined && input.ClinGen_inheritance_mode !== '') {
    query.push(`record.inheritance_mode == '${input.ClinGen_inheritance_mode}'`)
    delete input.ClinGen_inheritance_mode
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
  delete input.organism
  if (input.disease_id === undefined && input.term_name === undefined) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'disease_id or term_name must be defined.'
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
  delete input.organism
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

  const verboseQueryORPHANET = `
    FOR otherRecord IN ${diseaseSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(diseaseSchema).replaceAll('record', 'otherRecord')}}
  `

  const verboseQueryDiseaseClinGen = `
    FOR otherRecord IN ${diseaseSchema.db_collection_name as string}
    FILTER otherRecord._key == PARSE_IDENTIFIER(edgeRecord._to).key
    RETURN {${getDBReturnStatements(diseaseSchema).replaceAll('record', 'otherRecord')}}
  `
  const verboseQueryVariantClinGen = `
  FOR otherRecord IN ${variantSchema.db_collection_name as string}
  FILTER otherRecord._key == PARSE_IDENTIFIER(edgeRecord._from).key
  RETURN {${getDBReturnStatements(variantSchema, true).replaceAll('record', 'otherRecord')}}
`
  const geneQuery = `
    LET targets = (
      FOR record IN ${geneSchema.db_collection_name as string}
      FILTER ${getFilterStatements(geneSchema, preProcessRegionParam(input))}
      RETURN record._id
    )`

  const orphanetQuery = `
     LET ORPHANET = (
    FOR record IN ${diseaseToGeneSchema.db_collection_name as string}
      FILTER record._to IN targets ${customFilter}
      SORT record._key
      RETURN {
        'disease': ${input.verbose === 'true' ? `(${verboseQueryORPHANET})[0]` : 'record._from'},
        ${getDBReturnStatements(diseaseToGeneSchema)}
      }
    )
  `

  const clinGenQuery = `
  LET CLINGEN = (
    FOR record IN ${variantToDiseaseToGeneSchema.db_collection_name as string}
      FILTER record._to IN targets ${customFilter}
      SORT record._key
      RETURN (
        FOR edgeRecord IN ${variantToDiseaseSchema.db_collection_name as string}
        FILTER edgeRecord._key == PARSE_IDENTIFIER(record._from).key
        RETURN {
          'disease': edgeRecord._to,
          'term_name': DOCUMENT(edgeRecord._to)['name'],
          ${getDBReturnStatements(variantToDiseaseToGeneSchema)}
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
    FOR record IN ${variantToDiseaseToGeneSchema.db_collection_name as string}
      FILTER record._to IN targets ${customFilter}
      SORT record._key
      RETURN (
        FOR edgeRecord IN ${variantToDiseaseSchema.db_collection_name as string}
        FILTER edgeRecord._key == PARSE_IDENTIFIER(record._from).key
        RETURN {
          'variant': ${`(${verboseQueryVariantClinGen})[0]`},
          'disease': ${`(${verboseQueryDiseaseClinGen})[0]`},
          ${getDBReturnStatements(variantToDiseaseToGeneSchema)}
        }
      )[0]
    )

  LET CLINGENUNIQ = (
    FOR record IN CLINGEN
    COLLECT disease = record.disease, inheritance_mode = record.inheritance_mode, source = record.source, source_url = record.source_url INTO variants = record.variant
    RETURN {
      'variants': variants,
      'disease': disease,
      'inheritance_mode': inheritance_mode,
      'source': source,
      'source_url': source_url
    }
  )

  `
  const query = `
    ${geneQuery}
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
