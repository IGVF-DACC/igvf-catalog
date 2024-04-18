import { z } from 'zod'
import { db } from '../../../database'
import { QUERY_LIMIT } from '../../../constants'
import { publicProcedure } from '../../../trpc'
import { loadSchemaConfig } from '../../genericRouters/genericRouters'
import { variantFormat, variantsQueryFormat } from '../nodes/variants'
import { drugFormat, drugsQueryFormat } from '../nodes/drugs'
import { getDBReturnStatements, getFilterStatements, paramsFormatType } from '../_helpers'
import { TRPCError } from '@trpc/server'
import { descriptions } from '../descriptions'

const MAX_PAGE_SIZE = 100

const schema = loadSchemaConfig()
const variantToDrugSchemaObj = schema['variant to drug']
const drugSchemaObj = schema.drug
const variantSchemaObj = schema['sequence variant']

const variantsToDrugsQueryFormat = z.object({
  pmid: z.string().trim().optional(),
  phenotype_categories: z.string().trim().optional(),
  verbose: z.enum(['true', 'false']).default('false'),
  limit: z.number().optional()
})

const studyParametersDict = z.object({
  study_parameter_id: z.string(),
  study_type: z.string().optional(),
  study_cases: z.string().optional(),
  study_controls: z.string().optional(),
  'p-value': z.string().optional(),
  biogeographical_groups: z.string().optional()
})

const variantsToDrugsFormat = z.object({
  drug: z.string().or(z.array(drugFormat)).optional(),
  _from: z.string(),
  gene_symbol: z.array(z.string()).optional(),
  pmid: z.string().optional(),
  study_parameters: z.array(studyParametersDict).optional(),
  phenotype_categories: z.array(z.string()).optional(),
  source: z.string(),
  source_url: z.string()
}).transform(({ _from, ...rest }) => ({ 'sequence variant': _from, ...rest }))

const drugsToVariantsFormat = z.object({
  'sequence variant': z.string().or(variantFormat).optional(),
  _to: z.string(),
  gene_symbol: z.array(z.string()).optional(),
  pmid: z.string().optional(),
  study_parameters: z.array(studyParametersDict).optional(),
  phenotype_categories: z.array(z.string()).optional(),
  source: z.string(),
  source_url: z.string()
}).transform(({ _to, ...rest }) => ({ drug: _to, ...rest }))

function edgeQuery (input: paramsFormatType): string {
  const query = []

  if (input.pmid !== undefined && input.pmid !== '') {
    query.push(`record.pmid == '${input.pmid}'`)
    delete input.pmid
  }

  if (input.phenotype_categories !== undefined && input.phenotype_categories !== '') {
    query.push(`'${input.phenotype_categories}' IN record.phenotype_categories`)
    delete input.phenotype_categories
  }

  if (Object.keys(input).filter(item => !['page', 'verbose'].includes(item)).length === 0) {
    throw new TRPCError({
      code: 'BAD_REQUEST',
      message: 'At least one node property for variant / drug must be defined.'
    })
  }

  return query.join(' and ')
}

async function variantsFromDrugSearch (input: paramsFormatType): Promise<any[]> {
  if (input.drug_id !== undefined) {
    input._id = `drugs/${input.drug_id}`
    delete input.drug_id
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

  const verbose = input.verbose === 'true'

  const variantVerboseQuery = `
    FOR otherRecord IN ${variantSchemaObj.db_collection_name}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._from).key
    RETURN {${getDBReturnStatements(variantSchemaObj).replaceAll('record', 'otherRecord')}}
  `

  const query = `
    LET drugs = (
      FOR record IN ${drugSchemaObj.db_collection_name}
      FILTER ${getFilterStatements(drugSchemaObj, input)}
      RETURN record._id
    )

    FOR record IN ${variantToDrugSchemaObj.db_collection_name}
      FILTER record._to IN drugs ${customFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        ${getDBReturnStatements(variantToDrugSchemaObj)},
        'sequence variant': ${verbose ? `(${variantVerboseQuery})[0]` : 'record._from'}
      }
  `

  return await (await db.query(query)).all()
}

async function drugsFromVariantSearch (input: paramsFormatType): Promise<any []> {
  if (input.variant_id !== undefined) {
    input._id = `variants/${input.variant_id}`
    delete input.variant_id
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

  const verbose = input.verbose === 'true'

  const drugVerboseQuery = `
    FOR otherRecord IN ${drugSchemaObj.db_collection_name}
    FILTER otherRecord._key == PARSE_IDENTIFIER(record._to).key
    RETURN {${getDBReturnStatements(drugSchemaObj).replaceAll('record', 'otherRecord')}}
  `

  const query = `
    LET variantIDs = (
      FOR record in ${variantSchemaObj.db_collection_name}
      FILTER ${getFilterStatements(variantSchemaObj, input)}
      RETURN record._id
    )

    FOR record IN ${variantToDrugSchemaObj.db_collection_name}
      FILTER record._from IN variantIDs ${customFilter}
      SORT record._key
      LIMIT ${input.page as number * limit}, ${limit}
      RETURN {
        ${getDBReturnStatements(variantToDrugSchemaObj)},
        'drug': ${verbose ? `(${drugVerboseQuery})` : 'record._to'}
      }
  `

  return await (await db.query(query)).all()
}

const drugsQuery = drugsQueryFormat.merge(
  variantsToDrugsQueryFormat
).merge(z.object({drug_name: z.string().trim().optional()})).omit({
  name: true
}).transform(({ drug_name, ...rest }) => ({ name: drug_name, ...rest }))

const variantsFromDrugs = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/drugs/variants', description: descriptions.drugs_variants } })
  .input(drugsQuery)
  .output(z.array(drugsToVariantsFormat))
  .query(async ({ input }) => await variantsFromDrugSearch(input))

const drugsFromVariants = publicProcedure
  .meta({ openapi: { method: 'GET', path: '/variants/drugs', description: descriptions.variants_drugs } })
  .input(variantsQueryFormat.omit({ region: true, funseq_description: true }).merge(variantsToDrugsQueryFormat))
  .output(z.array(variantsToDrugsFormat))
  .query(async ({ input }) => await drugsFromVariantSearch(input))

export const variantsDrugsRouters = {
  variantsFromDrugs,
  drugsFromVariants
}
